from agec import AGECBlockedError, guard


@guard(
    intent="send_email",
    purpose="customer_support",
    allowed_tools=["gmail.send"],
    legal_basis="consent",
)
def send_email() -> str:
    return "Email sent."


@guard(
    intent="transfer_money",
    purpose="unknown",
    allowed_tools=["bank.transfer"],
    legal_basis="consent",
    intent_confidence=0.48,
)
def unsafe_transfer() -> str:
    return "Transferred $1M."


if __name__ == "__main__":
    print(send_email())

    try:
        print(unsafe_transfer())
    except AGECBlockedError as exc:
        print("AGEC BLOCKED EXECUTION")
        print(f"Reason: {exc.reason}")
        print(f"Audit ID: {exc.agec.agec_id}")
        print("Replayable: yes")
