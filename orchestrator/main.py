import grpc
import time
import os
from concurrent import futures

import order_pb2
import order_pb2_grpc
import kitchen_pb2
import kitchen_pb2_grpc
import accounting_pb2
import accounting_pb2_grpc

ORDER_SERVICE_HOST     = os.getenv("ORDER_SERVICE_HOST",      "order-service:50051")
KITCHEN_SERVICE_HOST   = os.getenv("KITCHEN_SERVICE_HOST",    "kitchen-service:50052")
ACCOUNTING_SERVICE_HOST = os.getenv("ACCOUNTING_SERVICE_HOST", "accounting-service:50053")


def run_saga(order_id: str, amount: float):
    print(f"\n🚀 Starting Saga for order [{order_id}] amount: {amount}")

    # --- Connect to all 3 services ---
    order_channel      = grpc.insecure_channel(ORDER_SERVICE_HOST)
    kitchen_channel    = grpc.insecure_channel(KITCHEN_SERVICE_HOST)
    accounting_channel = grpc.insecure_channel(ACCOUNTING_SERVICE_HOST)

    order_stub      = order_pb2_grpc.OrderServiceStub(order_channel)
    kitchen_stub    = kitchen_pb2_grpc.KitchenServiceStub(kitchen_channel)
    accounting_stub = accounting_pb2_grpc.AccountingServiceStub(accounting_channel)

    try:
        # --- Step 1: Set order to APPROVAL_PENDING ---
        print("\n--- Step 1: Setting status to APPROVAL_PENDING ---")
        order_stub.UpdateStatus(order_pb2.UpdateStatusRequest(
            orderId=order_id,
            status="APPROVAL_PENDING"
        ))

        # --- Step 2: Create Kitchen Ticket ---
        print("\n--- Step 2: Creating Kitchen Ticket ---")
        ticket_response = kitchen_stub.CreateTicket(kitchen_pb2.TicketRequest(
            orderId=order_id
        ))

        if not ticket_response.success:
            raise Exception(f"Kitchen ticket creation failed for order [{order_id}]")

        # --- Step 3: Authorize Payment ---
        print("\n--- Step 3: Authorizing Payment ---")
        auth_response = accounting_stub.AuthorizeCard(accounting_pb2.AuthorizeRequest(
            orderId=order_id,
            amount=amount
        ))

        # --- Step 4: Happy Path or Compensation ---
        if auth_response.authorized:
            print("\n--- Step 4: HAPPY PATH — Setting status to APPROVED ---")
            order_stub.UpdateStatus(order_pb2.UpdateStatusRequest(
                orderId=order_id,
                status="APPROVED"
            ))
            print(f"\n✅ Order [{order_id}] successfully APPROVED!")
            return {"success": True, "status": "APPROVED"}

        else:
            print("\n--- Step 4: COMPENSATION — Payment not authorized ---")

            print("--- Rejecting Kitchen Ticket ---")
            kitchen_stub.RejectTicket(kitchen_pb2.RejectRequest(
                orderId=order_id
            ))

            print("--- Setting status to REJECTED ---")
            order_stub.UpdateStatus(order_pb2.UpdateStatusRequest(
                orderId=order_id,
                status="REJECTED"
            ))
            print(f"\n❌ Order [{order_id}] REJECTED — amount >= 100")
            return {"success": False, "status": "REJECTED"}

    except Exception as e:
        print(f"\n💥 Saga failed with error: {e}")
        # Compensation on unexpected error
        try:
            kitchen_stub.RejectTicket(kitchen_pb2.RejectRequest(orderId=order_id))
            order_stub.UpdateStatus(order_pb2.UpdateStatusRequest(
                orderId=order_id,
                status="REJECTED"
            ))
        except:
            pass
        return {"success": False, "status": "REJECTED", "error": str(e)}

    finally:
        order_channel.close()
        kitchen_channel.close()
        accounting_channel.close()


if __name__ == "__main__":
    # For testing: run a saga directly
    import sys
    if len(sys.argv) >= 3:
        order_id = sys.argv[1]
        amount   = float(sys.argv[2])
    else:
        order_id = "test-001"
        amount   = 50.0

    print("⏳ Waiting for services to be ready...")
    time.sleep(5)
    run_saga(order_id, amount)