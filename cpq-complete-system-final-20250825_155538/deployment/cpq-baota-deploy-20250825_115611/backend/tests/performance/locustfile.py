"""
Performance tests for CPQ API using Locust.
"""

from locust import HttpUser, task, between
import json
import random


class CPQUser(HttpUser):
    """Simulate CPQ system user behavior."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts - perform login."""
        self.login()
    
    def login(self):
        """Login user and store authentication token."""
        response = self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("tokens", {}).get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # Create user if login fails
            self.register()
    
    def register(self):
        """Register a new user if login fails."""
        username = f"perfuser_{random.randint(1000, 9999)}"
        response = self.client.post("/api/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "testpass123",
            "first_name": "Perf",
            "last_name": "User"
        })
        
        if response.status_code == 201:
            data = response.json()
            self.token = data.get("tokens", {}).get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_products(self):
        """Get products list - most common operation."""
        with self.client.get("/api/products", 
                           headers=getattr(self, 'headers', {}),
                           catch_response=True) as response:
            if response.status_code == 401:
                self.login()
                response.failure("Authentication failed")
            elif response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
            else:
                # Validate response structure
                try:
                    data = response.json()
                    if "products" not in data or "pagination" not in data:
                        response.failure("Invalid response structure")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
    
    @task(1)
    def get_product_detail(self):
        """Get individual product details."""
        # Assume product IDs 1-10 exist
        product_id = random.randint(1, 10)
        
        with self.client.get(f"/api/products/{product_id}",
                           headers=getattr(self, 'headers', {}),
                           catch_response=True) as response:
            if response.status_code == 401:
                self.login()
                response.failure("Authentication failed")
            elif response.status_code == 404:
                response.success()  # 404 is acceptable for non-existent products
            elif response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def get_quotes(self):
        """Get quotes list."""
        with self.client.get("/api/quotes",
                           headers=getattr(self, 'headers', {}),
                           catch_response=True) as response:
            if response.status_code == 401:
                self.login()
                response.failure("Authentication failed")
            elif response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
            else:
                try:
                    data = response.json()
                    if "quotes" not in data:
                        response.failure("Invalid response structure")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
    
    @task(1)
    def create_quote(self):
        """Create a new quote."""
        quote_data = {
            "customer_name": f"Perf Customer {random.randint(1, 1000)}",
            "customer_email": f"perf{random.randint(1, 1000)}@example.com",
            "customer_company": f"Perf Corp {random.randint(1, 100)}",
            "product_id": random.randint(1, 5),
            "quantity": random.randint(1, 10),
            "configuration": {
                "cpu": random.choice(["Intel i5", "Intel i7", "AMD Ryzen 5"]),
                "memory": random.choice(["8GB", "16GB", "32GB"])
            },
            "notes": f"Performance test quote {random.randint(1, 1000)}"
        }
        
        with self.client.post("/api/quotes",
                            json=quote_data,
                            headers=getattr(self, 'headers', {}),
                            catch_response=True) as response:
            if response.status_code == 401:
                self.login()
                response.failure("Authentication failed")
            elif response.status_code == 201:
                response.success()
            elif response.status_code == 400:
                # Validation errors are acceptable
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def search_products(self):
        """Search products by various criteria."""
        search_params = [
            {"category": "Electronics"},
            {"is_active": "true"},
            {"search": "laptop"},
            {"page": "1", "per_page": "5"}
        ]
        
        params = random.choice(search_params)
        
        with self.client.get("/api/products",
                           params=params,
                           headers=getattr(self, 'headers', {}),
                           catch_response=True) as response:
            if response.status_code == 401:
                self.login()
                response.failure("Authentication failed")
            elif response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def get_categories(self):
        """Get product categories."""
        with self.client.get("/api/products/categories",
                           headers=getattr(self, 'headers', {}),
                           catch_response=True) as response:
            if response.status_code == 401:
                self.login()
                response.failure("Authentication failed")
            elif response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
            else:
                try:
                    data = response.json()
                    if "categories" not in data:
                        response.failure("Invalid response structure")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")


class AdminUser(HttpUser):
    """Simulate admin user behavior with product management operations."""
    
    wait_time = between(2, 5)
    weight = 1  # Lower weight means fewer admin users
    
    def on_start(self):
        """Login as admin user."""
        response = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "adminpass123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("tokens", {}).get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(2)
    def manage_products(self):
        """Perform product management operations."""
        if not hasattr(self, 'headers'):
            return
        
        # Create product
        product_data = {
            "name": f"Perf Product {random.randint(1, 1000)}",
            "code": f"PERF-{random.randint(1000, 9999)}",
            "description": "Performance test product",
            "category": "Testing",
            "base_price": random.uniform(100, 5000),
            "is_active": True,
            "is_configurable": random.choice([True, False])
        }
        
        with self.client.post("/api/products",
                            json=product_data,
                            headers=self.headers,
                            catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                # Store product ID for potential updates/deletes
                data = response.json()
                product_id = data.get("product", {}).get("id")
                if product_id:
                    self.update_product(product_id)
            elif response.status_code == 400:
                # Validation errors are acceptable
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    def update_product(self, product_id):
        """Update a product."""
        update_data = {
            "description": f"Updated description {random.randint(1, 1000)}",
            "base_price": random.uniform(100, 5000)
        }
        
        with self.client.put(f"/api/products/{product_id}",
                           json=update_data,
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def approve_quotes(self):
        """Approve pending quotes."""
        if not hasattr(self, 'headers'):
            return
        
        # Get quotes that might need approval
        with self.client.get("/api/quotes?status=pending",
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                quotes = data.get("quotes", [])
                
                if quotes:
                    quote_id = random.choice(quotes)["id"]
                    # Approve the quote
                    with self.client.put(f"/api/quotes/{quote_id}/approve",
                                       json={"notes": "Performance test approval"},
                                       headers=self.headers,
                                       catch_response=True) as approve_response:
                        if approve_response.status_code in [200, 404, 400]:
                            approve_response.success()
                        else:
                            approve_response.failure(f"Got status code {approve_response.status_code}")


class HealthCheckUser(HttpUser):
    """Lightweight user for health check monitoring."""
    
    wait_time = between(5, 10)
    weight = 1
    
    @task
    def health_check(self):
        """Check API health endpoint."""
        with self.client.get("/api/health",
                           catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure("Unhealthy status")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")