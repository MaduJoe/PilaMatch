import os
import httpx
from typing import Optional, Dict, Any

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class APIClient:
    def __init__(self, token: Optional[str] = None):
        self.base_url = f"{API_BASE_URL}/api/v1"
        self.token = token

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                f"{self.base_url}{endpoint}",
                json=data,
                params=params,
                headers=self._headers(),
                timeout=30.0,
            )
            if response.status_code >= 400:
                error = response.json()
                raise APIError(response.status_code, error)
            if response.status_code == 204:
                return {}
            return response.json()

    def _request_sync(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        try:
            with httpx.Client() as client:
                response = client.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    json=data,
                    params=params,
                    headers=self._headers(),
                    timeout=30.0,
                )
                if response.status_code >= 400:
                    try:
                        error = response.json()
                    except:
                        error = {"detail": {"code": "API_ERROR", "message": f"HTTP {response.status_code}: {response.text or 'No response'}"}}
                    raise APIError(response.status_code, error)
                if response.status_code == 204:
                    return {}
                return response.json()
        except httpx.ConnectError:
            raise APIError(503, {"detail": {"code": "CONNECTION_ERROR", "message": "Cannot connect to API server. Is the backend running?"}})

    # Auth
    def signup(self, email: str, password: str, role: str, display_name: str = None, business_name: str = None):
        data = {"email": email, "password": password, "role": role}
        if display_name:
            data["display_name"] = display_name
        if business_name:
            data["business_name"] = business_name
        return self._request_sync("POST", "/auth/signup", data)

    def login(self, email: str, password: str):
        return self._request_sync("POST", "/auth/login", {"email": email, "password": password})

    def get_me(self):
        return self._request_sync("GET", "/auth/me")

    # Profiles
    def get_my_instructor_profile(self):
        return self._request_sync("GET", "/instructors/me")

    def update_instructor_profile(self, data: Dict):
        return self._request_sync("PUT", "/instructors/me", data)

    def get_my_studio_profile(self):
        return self._request_sync("GET", "/studios/me")

    def update_studio_profile(self, data: Dict):
        return self._request_sync("PUT", "/studios/me", data)

    def get_instructor(self, instructor_id: str):
        return self._request_sync("GET", f"/instructors/{instructor_id}")

    def get_studio(self, studio_id: str):
        return self._request_sync("GET", f"/studios/{studio_id}")

    # Job Posts
    def create_job_post(self, data: Dict):
        return self._request_sync("POST", "/job-posts", data)

    def list_job_posts(self, params: Optional[Dict] = None):
        return self._request_sync("GET", "/job-posts", params=params)

    def list_job_posts_with_matching(self, params: Optional[Dict] = None):
        """List job posts with matching scores for instructors."""
        return self._request_sync("GET", "/job-posts/for-me/with-matching", params=params)

    def get_job_post(self, job_post_id: str):
        return self._request_sync("GET", f"/job-posts/{job_post_id}")

    def update_job_post(self, job_post_id: str, data: Dict):
        return self._request_sync("PUT", f"/job-posts/{job_post_id}", data)

    def delete_job_post(self, job_post_id: str):
        return self._request_sync("DELETE", f"/job-posts/{job_post_id}")

    # Applications
    def apply_to_job(self, job_post_id: str, cover_letter: str = None):
        data = {}
        if cover_letter:
            data["cover_letter"] = cover_letter
        return self._request_sync("POST", f"/job-posts/{job_post_id}/applications", data)

    def get_my_applications(self):
        return self._request_sync("GET", "/applications/me")

    def withdraw_application(self, application_id: str):
        return self._request_sync("POST", f"/applications/{application_id}/withdraw")

    def get_job_post_applications(self, job_post_id: str):
        """Get all applications for a job post (studio owner only)."""
        return self._request_sync("GET", f"/job-posts/{job_post_id}/applications")

    # Offers
    def create_offer(self, data: Dict):
        return self._request_sync("POST", "/offers", data)

    def get_my_offers(self):
        return self._request_sync("GET", "/offers/me")

    def accept_offer(self, offer_id: str):
        return self._request_sync("POST", f"/offers/{offer_id}/accept")

    def reject_offer(self, offer_id: str):
        return self._request_sync("POST", f"/offers/{offer_id}/reject")

    # Contracts
    def create_contract_from_offer(self, offer_id: str):
        return self._request_sync("POST", f"/contracts/from-offer/{offer_id}")

    def get_my_contracts(self):
        return self._request_sync("GET", "/contracts/me")

    def set_contract_in_progress(self, contract_id: str):
        return self._request_sync("POST", f"/contracts/{contract_id}/set-in-progress")

    def complete_contract(self, contract_id: str):
        """Confirm contract completion (v2.0 - bidirectional confirmation)."""
        return self._request_sync("POST", f"/contracts/{contract_id}/confirm-completion")

    def cancel_contract(self, contract_id: str, reason: str):
        return self._request_sync("POST", f"/contracts/{contract_id}/cancel", {"reason": reason})

    def report_no_show(self, contract_id: str, reported_user_id: str):
        """Report a no-show for a contract."""
        return self._request_sync("POST", f"/contracts/{contract_id}/report-no-show", {
            "reported_user_id": reported_user_id
        })

    # Payments
    def initialize_payment(self, contract_id: str):
        return self._request_sync("POST", f"/contracts/{contract_id}/payments")

    def confirm_payment(self, payment_key: str, order_id: str, amount: float):
        return self._request_sync("POST", "/payments/confirm", {
            "payment_key": payment_key,
            "order_id": order_id,
            "amount": amount,
        })

    # Chat
    def get_threads(self):
        return self._request_sync("GET", "/threads")

    def create_thread(self, data: Dict):
        return self._request_sync("POST", "/threads", data)

    def get_thread_messages(self, thread_id: str):
        return self._request_sync("GET", f"/threads/{thread_id}/messages")

    def send_message(self, thread_id: str, content: str):
        return self._request_sync("POST", f"/threads/{thread_id}/messages", {"content": content})

    # Reviews
    def create_review(self, contract_id: str, rating: int, comment: str = None):
        data = {"rating": rating}
        if comment:
            data["comment"] = comment
        return self._request_sync("POST", f"/contracts/{contract_id}/reviews", data)

    def get_my_review_for_contract(self, contract_id: str):
        """Get current user's review for a specific contract."""
        return self._request_sync("GET", f"/contracts/{contract_id}/reviews/my")

    def update_review(self, review_id: str, rating: int = None, comment: str = None):
        """Update an existing review."""
        data = {}
        if rating is not None:
            data["rating"] = rating
        if comment is not None:
            data["comment"] = comment
        return self._request_sync("PUT", f"/reviews/{review_id}", data)

    def delete_review(self, review_id: str):
        """Delete a review."""
        return self._request_sync("DELETE", f"/reviews/{review_id}")

    # Support
    def create_support_ticket(self, subject: str, description: str):
        return self._request_sync("POST", "/support/tickets", {
            "subject": subject,
            "description": description,
        })

    def get_my_support_tickets(self):
        return self._request_sync("GET", "/support/tickets/me")

    # Verification
    def request_phone_verification(self, phone: str):
        return self._request_sync("POST", "/verification/phone/request", {"phone": phone})

    def verify_phone(self, phone: str, otp: str):
        return self._request_sync("POST", "/verification/phone/verify", {"phone": phone, "otp": otp})

    def verify_business(self, business_number: str):
        return self._request_sync("POST", "/verification/business/verify", {"business_number": business_number})

    def get_verification_status(self):
        return self._request_sync("GET", "/verification/status")

    # Deposit
    def get_deposit_status(self):
        return self._request_sync("GET", "/deposit/status")

    def add_deposit(self, amount: float):
        return self._request_sync("POST", "/deposit/add", {"amount": amount})

    # Subscription (Premium Membership)
    def get_subscription_status(self):
        """Get current user's subscription status."""
        return self._request_sync("GET", "/subscriptions/me")

    def initialize_premium_upgrade(self):
        """Initialize premium subscription upgrade."""
        return self._request_sync("POST", "/subscriptions/upgrade", {})

    def confirm_subscription_payment(self, payment_key: str, order_id: str):
        """Confirm subscription payment after TossPayments."""
        return self._request_sync("POST", "/subscriptions/confirm", {
            "payment_key": payment_key,
            "order_id": order_id,
        })

    def cancel_subscription(self, reason: str = None):
        """Cancel active premium subscription."""
        data = {}
        if reason:
            data["reason"] = reason
        return self._request_sync("POST", "/subscriptions/cancel", data)

    def get_subscription_history(self):
        """Get subscription change history."""
        return self._request_sync("GET", "/subscriptions/history")


class APIError(Exception):
    def __init__(self, status_code: int, detail: Dict):
        self.status_code = status_code
        self.detail = detail

        # Handle different error formats
        detail_content = detail.get("detail")
        if isinstance(detail_content, list):
            # FastAPI validation error format
            errors = [f"{e.get('loc', ['?'])[-1]}: {e.get('msg', 'error')}" for e in detail_content]
            self.code = "VALIDATION_ERROR"
            self.message = "; ".join(errors)
        elif isinstance(detail_content, dict):
            # Custom error format
            self.code = detail_content.get("code", "UNKNOWN_ERROR")
            self.message = detail_content.get("message", str(detail))
        elif isinstance(detail_content, str):
            self.code = "ERROR"
            self.message = detail_content
        else:
            self.code = "UNKNOWN_ERROR"
            self.message = str(detail)

        super().__init__(self.message)
