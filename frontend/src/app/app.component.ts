import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  // Form fields
  orderId: string = '';
  amount: number = 0;

  // Search field
  searchOrderId: string = '';

  // Results
  orderResult: any = null;
  orderStatus: any = null;
  loading: boolean = false;
  errorMessage: string = '';

  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  generateOrderId() {
    this.orderId = 'ORD-' + Math.random().toString(36).substring(2, 8).toUpperCase();
  }

  createOrder() {
    if (!this.orderId || !this.amount) {
      this.errorMessage = 'Please fill in all fields.';
      return;
    }
    this.loading = true;
    this.orderResult = null;
    this.errorMessage = '';

    this.http.post(`${this.apiUrl}/orders`, {
      orderId: this.orderId,
      amount: this.amount
    }).subscribe({
      next: (res) => {
        this.orderResult = res;
        this.loading = false;
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Something went wrong.';
        this.loading = false;
      }
    });
  }

  getOrderStatus() {
    if (!this.searchOrderId) return;
    this.loading = true;
    this.orderStatus = null;

    this.http.get(`${this.apiUrl}/orders/${this.searchOrderId}`).subscribe({
      next: (res) => {
        this.orderStatus = res;
        this.loading = false;
      },
      error: (err) => {
        this.errorMessage = 'Order not found.';
        this.loading = false;
      }
    });
  }
}