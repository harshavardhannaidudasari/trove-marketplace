import { useState, type FormEvent } from "react";
import { PaymentElement, useElements, useStripe } from "@stripe/react-stripe-js";

export function PaymentForm({ onPaid, total }: { onPaid: (paymentIntentId: string) => void; total: string }) {
  const stripe = useStripe();
  const elements = useElements();
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!stripe || !elements) return;
    setProcessing(true);
    setError(null);

    const { error: submitError, paymentIntent } = await stripe.confirmPayment({
      elements,
      redirect: "if_required",
    });

    if (submitError) {
      setError(submitError.message ?? "Payment failed");
      setProcessing(false);
      return;
    }
    if (paymentIntent && (paymentIntent.status === "succeeded" || paymentIntent.status === "processing")) {
      onPaid(paymentIntent.id);
    } else {
      setError("Payment did not complete");
      setProcessing(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="glass payment-form" style={{ padding: 24 }}>
      <PaymentElement />
      {error && <p className="error-text" style={{ marginTop: 14 }}>{error}</p>}
      <button className="btn btn-primary btn-block" type="submit" disabled={!stripe || processing} style={{ marginTop: 20 }}>
        {processing ? <span className="spinner" /> : `Pay ${total}`}
      </button>
      <p style={{ fontSize: 12, color: "var(--text-faint)", marginTop: 12 }}>
        Test mode — use card <strong>4242 4242 4242 4242</strong>, any future expiry, any CVC.
      </p>
    </form>
  );
}
