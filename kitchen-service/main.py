import grpc
from concurrent import futures
from sqlalchemy.orm import Session

import kitchen_pb2
import kitchen_pb2_grpc
from database import engine, SessionLocal
from models import Base, KitchenTicket

Base.metadata.create_all(bind=engine)

class KitchenServicer(kitchen_pb2_grpc.KitchenServiceServicer):

    def CreateTicket(self, request, context):
        db: Session = SessionLocal()
        try:
            ticket = db.query(KitchenTicket).filter(
                KitchenTicket.order_id == request.orderId
            ).first()
            if ticket:
                ticket.status = "CREATED"
            else:
                ticket = KitchenTicket(order_id=request.orderId, status="CREATED")
                db.add(ticket)
            db.commit()
            print(f"[Kitchen] Ticket CREATED for order {request.orderId}")
            return kitchen_pb2.TicketResponse(success=True)
        except Exception as e:
            print(f"[Kitchen] ERROR: {e}")
            return kitchen_pb2.TicketResponse(success=False)
        finally:
            db.close()

    def RejectTicket(self, request, context):
        db: Session = SessionLocal()
        try:
            ticket = db.query(KitchenTicket).filter(
                KitchenTicket.order_id == request.orderId
            ).first()
            if ticket:
                ticket.status = "REJECTED"
                db.commit()
            print(f"[Kitchen] Ticket REJECTED for order {request.orderId}")
            return kitchen_pb2.RejectResponse(acknowledged=True)
        except Exception as e:
            print(f"[Kitchen] ERROR: {e}")
            return kitchen_pb2.RejectResponse(acknowledged=False)
        finally:
            db.close()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kitchen_pb2_grpc.add_KitchenServiceServicer_to_server(KitchenServicer(), server)
    server.add_insecure_port("[::]:50052")
    server.start()
    print("[Kitchen Service] listening on port 50052")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()