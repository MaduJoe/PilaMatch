"""TossPayments JS SDK v2 widget for Streamlit."""

import os
import streamlit as st
import streamlit.components.v1 as components


def _is_mock_mode(client_key: str) -> bool:
    """Check if we should use mock mode based on client key."""
    if not client_key:
        return True
    if len(client_key) < 20:
        return True
    if "xxxx" in client_key.lower():
        return True
    return False


def render_toss_payment_widget(
    client_key: str,
    order_id: str,
    order_name: str,
    amount: int,
    customer_key: str,
    payment_type: str = "contract",
    success_url: str = "",
    fail_url: str = "",
    height: int = 580,
):
    """Render TossPayments payment widget.

    Args:
        client_key: TossPayments client key
        order_id: Unique order ID
        order_name: Display name for the order
        amount: Payment amount in KRW
        customer_key: Customer identifier
        payment_type: "contract" or "subscription"
        success_url: Backend success redirect URL
        fail_url: Backend fail redirect URL
        height: iframe height in pixels
    """
    backend_url = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")

    if not success_url:
        success_url = f"{backend_url}/api/v1/payments/success?type={payment_type}"
    if not fail_url:
        fail_url = f"{backend_url}/api/v1/payments/fail?type={payment_type}"

    if _is_mock_mode(client_key):
        _render_mock_widget(order_id, order_name, amount, payment_type)
    else:
        _render_real_widget(
            client_key, order_id, order_name, amount,
            customer_key, success_url, fail_url, height,
        )


def _render_mock_widget(
    order_id: str, order_name: str, amount: int, payment_type: str,
):
    """Render mock payment widget for development/testing."""
    st.info("테스트 모드: 토스페이먼츠 키가 설정되지 않아 모의 결제를 진행합니다.")

    with st.container():
        st.markdown(f"""
**결제 정보**
- 주문명: {order_name}
- 결제금액: ₩{amount:,}
- 주문번호: `{order_id}`
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "테스트 결제 완료",
                key=f"mock_pay_{order_id}",
                type="primary",
                use_container_width=True,
            ):
                mock_payment_key = f"mock_pk_{order_id}"
                st.session_state[f"payment_completed_{order_id}"] = {
                    "payment_key": mock_payment_key,
                    "order_id": order_id,
                    "amount": amount,
                    "type": payment_type,
                }
                st.rerun()
        with col2:
            if st.button(
                "취소",
                key=f"mock_cancel_{order_id}",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state[f"payment_cancelled_{order_id}"] = True
                st.rerun()


def _render_real_widget(
    client_key: str,
    order_id: str,
    order_name: str,
    amount: int,
    customer_key: str,
    success_url: str,
    fail_url: str,
    height: int,
):
    """Render real TossPayments JS SDK v2 payment widget."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <script src="https://js.tosspayments.com/v2/standard"></script>
    <style>
        body {{
            margin: 0;
            padding: 16px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #fafafa;
        }}
        .payment-info {{
            background: white;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid #e0e0e0;
        }}
        .payment-info h3 {{
            margin: 0 0 8px 0;
            font-size: 16px;
        }}
        .payment-info p {{
            margin: 4px 0;
            color: #666;
            font-size: 14px;
        }}
        .amount {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        #payment-method {{
            min-height: 300px;
        }}
        .pay-btn {{
            width: 100%;
            padding: 14px;
            background: #3182f6;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 16px;
        }}
        .pay-btn:hover {{
            background: #1b64da;
        }}
        .pay-btn:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        .error-msg {{
            color: #e74c3c;
            margin-top: 8px;
            font-size: 14px;
        }}
        @media (max-width: 640px) {{
            body {{ padding: 8px; }}
            .payment-info {{ padding: 12px; }}
            .payment-info h3 {{ font-size: 14px; }}
            .amount {{ font-size: 20px; }}
            .pay-btn {{ padding: 12px; font-size: 14px; }}
        }}
    </style>
</head>
<body>
    <div class="payment-info">
        <h3>{order_name}</h3>
        <p>주문번호: {order_id}</p>
        <p class="amount">₩{amount:,}</p>
    </div>

    <div id="payment-method"></div>
    <div id="agreement"></div>

    <button class="pay-btn" id="pay-button" onclick="requestPayment()">
        ₩{amount:,} 결제하기
    </button>
    <div id="error-message" class="error-msg"></div>

    <script>
        const clientKey = "{client_key}";
        const customerKey = "{customer_key}";

        let widgets;

        async function initWidgets() {{
            try {{
                const tossPayments = TossPayments(clientKey);
                widgets = tossPayments.widgets({{
                    customerKey: customerKey,
                }});

                await widgets.setAmount({{
                    currency: "KRW",
                    value: {amount},
                }});

                await Promise.all([
                    widgets.renderPaymentMethods({{
                        selector: "#payment-method",
                        variantKey: "DEFAULT",
                    }}),
                    widgets.renderAgreement({{
                        selector: "#agreement",
                        variantKey: "AGREEMENT",
                    }}),
                ]);
            }} catch (error) {{
                document.getElementById("error-message").textContent =
                    "결제 위젯 로드 실패: " + error.message;
            }}
        }}

        async function requestPayment() {{
            const btn = document.getElementById("pay-button");
            btn.disabled = true;
            btn.textContent = "결제 처리 중...";

            try {{
                await widgets.requestPayment({{
                    orderId: "{order_id}",
                    orderName: "{order_name}",
                    successUrl: "{success_url}",
                    failUrl: "{fail_url}",
                }});
            }} catch (error) {{
                // User cancelled or error
                btn.disabled = false;
                btn.textContent = "₩{amount:,} 결제하기";
                if (error.code === "USER_CANCEL") {{
                    // User cancelled - do nothing
                }} else {{
                    document.getElementById("error-message").textContent =
                        "결제 오류: " + error.message;
                }}
            }}
        }}

        // Initialize on load
        initWidgets();
    </script>
</body>
</html>
"""
    components.html(html_content, height=height, scrolling=True)
