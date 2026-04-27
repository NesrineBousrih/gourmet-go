import grpc
import time
from concurrent import futures
from sqlalchemy.orm import Session

import order_pb2
import order_pb2_grpc
from database import engine, SessionLocal
from models import Base, Order

Base.metadata.create_all(bind=engine)

class OrderServicer(order_pb2_grpc.OrderServiceServicer):

    def UpdateStatus(self, request, context):
        db: Session = SessionLocal()
        try:
            order = db.query(Order).filter(Order.order_id == request.orderId).first()
            if order:
                order.status = request.status
            else:
                order = Order(order_id=request.orderId, status=request.status)
                db.add(order)
            db.commit()
            print(f"[Order] {request.orderId} → {request.status}")
            return order_pb2.UpdateStatusResponse(acknowledged=True)
        except Exception as e:
            print(f"[Order] ERROR: {e}")
            return order_pb2.UpdateStatusResponse(acknowledged=False)
        finally:
            db.close()

    def GetStatus(self, request, context):
        db: Session = SessionLocal()
        try:
            order = db.query(Order).filter(Order.order_id == request.orderId).first()
            if order:
                return order_pb2.GetStatusResponse(
                    orderId=order.order_id,
                    status=order.status
                )
            else:
                return order_pb2.GetStatusResponse(
                    orderId=request.orderId,
                    status="NOT_FOUND"
                )
        finally:
            db.close()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("[Order Service] listening on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()