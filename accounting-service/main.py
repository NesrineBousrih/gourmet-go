import grpc
from concurrent import futures
from sqlalchemy.orm import Session

import accounting_pb2
import accounting_pb2_grpc
from database import engine, SessionLocal
from models import Base, Payment

Base.metadata.create_all(bind=engine)

class AccountingServicer(accounting_pb2_grpc.AccountingServiceServicer):

    def AuthorizeCard(self, request, context):
        db: Session = SessionLocal()
        try:
            # Business rule from Lab5: amount >= 100 → REJECTED
            authorized = request.amount < 100

            payment = db.query(Payment).filter(
                Payment.order_id == request.orderId
            ).first()
            if payment:
                payment.amount = request.amount
                payment.authorized = authorized
            else:
                payment = Payment(
                    order_id=request.orderId,
                    amount=request.amount,
                    authorized=authorized
                )
                db.add(payment)
            db.commit()

            status = "AUTHORIZED" if authorized else "REJECTED"
            print(f"[Accounting] Order {request.orderId} amount={request.amount} → {status}")
            return accounting_pb2.AuthorizeResponse(authorized=authorized)
        except Exception as e:
            print(f"[Accounting] ERROR: {e}")
            return accounting_pb2.AuthorizeResponse(authorized=False)
        finally:
            db.close()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    accounting_pb2_grpc.add_AccountingServiceServicer_to_server(AccountingServicer(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    print("[Accounting Service] listening on port 50053")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()