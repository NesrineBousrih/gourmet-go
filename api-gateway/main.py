import grpc
import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import order_pb2
import order_pb2_grpc
import kitchen_pb2
import kitchen_pb2_grpc
import accounting_pb2
import accounting_pb2_grpc

app = FastAPI(title="Gourmet-Go API Gateway")

# Allow Angular to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ORDER_SERVICE_HOST      = os.getenv("ORDER_SERVICE_HOST",       "order-service:50051")
KITCHEN_SERVICE_HOST    = os.getenv("KITCHEN_SERVICE_HOST",     "kitchen-service:50052")
ACCOUNTING_SERVICE_HOST = os.getenv("ACCOUNTING_SERVICE_HOST",  "accounting-service:50053")


# ---------- Request Models ----------
class CreateOrderRequest(BaseModel):
    orderId: str
    amount: float


# ---------- Helper: run the full Saga ----------
def run_saga(order_id: str, amount: float):
    order_channel      = grpc.insecure_channel(ORDER_SERVICE_HOST)
    kitchen_channel    = grpc.insecure_channel(KITCHEN_SERVICE_HOST)
    accounting_channel = grpc.insecure_channel(ACCOUNTING_SERVICE_HOST)

    order_stub      = order_pb2_grpc.OrderServiceStub(order_channel)
    kitchen_stub    = kitchen_pb2_grpc.KitchenServiceStub(kitchen_channel)
    accounting_stub = accounting_pb2_grpc.AccountingServiceStub(accounting_channel)

    try:
        # Step 1: APPROVAL_PENDING
        order_stub.UpdateStatus(order_pb2.UpdateStatusRequest(
            orderId=order_id, status="APPROVAL_PENDING"
        ))

        # Step 2: Create kitchen ticket
        ticket = kitchen_stub.CreateTicket(kitchen_pb2.TicketRequest(orderId=order_id))
        if not ticket.success:
            raise Exception("Kitchen ticket creation failed")

        # Step 3: Authorize payment
        auth = accounting_stub.AuthorizeCard(accounting_pb2.AuthorizeRequest(
            orderId=order_id, amount=amount
        ))

        # Step 4: Happy path or compensation
        if auth.authorized:
            order_stub.UpdateStatus(order_pb2.UpdateStatusRequest(
                orderId=order_id, status="APPROVED"
            ))
            return {"orderId": order_id, "status": "APPROVED", "success": True}
        else:
            kitchen_stub.RejectTicket(kitchen_pb2.RejectRequest(orderId=order_id))
            order_stub.UpdateStatus(order_pb2.UpdateStatusRequest(
                orderId=order_id, status="REJECTED"
            ))
            return {"orderId": order_id, "status": "REJECTED", "success": False}

    except Exception as e:
        try:
            kitchen_stub.RejectTicket(kitchen_pb2.RejectRequest(orderId=order_id))
            order_stub.UpdateStatus(order_pb2.UpdateStatusRequest(
                orderId=order_id, status="REJECTED"
            ))
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        order_channel.close()
        kitchen_channel.close()
        accounting_channel.close()


# ---------- Endpoints ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/orders")
def create_order(req: CreateOrderRequest):
    return run_saga(req.orderId, req.amount)


@app.get("/orders/{order_id}")
def get_order_status(order_id: str):
    channel = grpc.insecure_channel(ORDER_SERVICE_HOST)
    stub    = order_pb2_grpc.OrderServiceStub(channel)
    try:
        response = stub.GetStatus(order_pb2.GetStatusRequest(orderId=order_id))
        return {"orderId": response.orderId, "status": response.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        channel.close()