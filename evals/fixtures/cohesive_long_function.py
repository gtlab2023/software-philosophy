def render_invoice(invoice):
    lines = []
    lines.append(f"Invoice {invoice.number}")
    lines.append(f"Customer: {invoice.customer_name}")
    lines.append("")
    subtotal = 0
    for item in invoice.items:
        amount = item.quantity * item.unit_price
        subtotal += amount
        lines.append(f"{item.quantity} x {item.description}: {amount}")
    tax = subtotal * invoice.tax_rate
    total = subtotal + tax
    lines.append("")
    lines.append(f"Subtotal: {subtotal}")
    lines.append(f"Tax: {tax}")
    lines.append(f"Total: {total}")
    return "\n".join(lines)
