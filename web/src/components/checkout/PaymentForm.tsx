import { useState, type FormEvent } from "react";
import type { CheckoutRequest, PaymentMethodType } from "../../api/types";

type Props = {
  total: string;
  onSubmit: (payment: Omit<CheckoutRequest, "shipping_address_id">) => Promise<void>;
};

const TABS: { id: PaymentMethodType; label: string; icon: string }[] = [
  { id: "card", label: "Card", icon: "💳" },
  { id: "upi", label: "UPI", icon: "📱" },
  { id: "wallet", label: "Wallet", icon: "👛" },
  { id: "cod", label: "Cash on Delivery", icon: "💵" },
];

const WALLETS = [
  { id: "gpay", label: "Google Pay" },
  { id: "phonepe", label: "PhonePe" },
  { id: "paytm", label: "Paytm" },
  { id: "amazonpay", label: "Amazon Pay" },
  { id: "mobikwik", label: "MobiKwik" },
];

function detectBrand(digits: string): string {
  if (/^4/.test(digits)) return "VISA";
  if (/^5[1-5]/.test(digits)) return "Mastercard";
  if (/^3[47]/.test(digits)) return "Amex";
  if (/^6/.test(digits)) return "RuPay";
  return "";
}

function formatCardNumber(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 19);
  return digits.replace(/(.{4})/g, "$1 ").trim();
}

export function PaymentForm({ total, onSubmit }: Props) {
  const [tab, setTab] = useState<PaymentMethodType>("card");
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);

  const [cardNumber, setCardNumber] = useState("");
  const [cardName, setCardName] = useState("");
  const [expiry, setExpiry] = useState("");
  const [cvv, setCvv] = useState("");

  const [vpa, setVpa] = useState("");

  const [wallet, setWallet] = useState<string | null>(null);

  const cardDigits = cardNumber.replace(/\D/g, "");
  const brand = detectBrand(cardDigits);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    let payload: Omit<CheckoutRequest, "shipping_address_id">;

    if (tab === "card") {
      const [mm, yy] = expiry.split("/").map((s) => s.trim());
      const month = Number(mm);
      const year = Number(yy?.length === 2 ? `20${yy}` : yy);
      if (!cardDigits || cardDigits.length < 13) return setError("Enter a valid card number");
      if (!month || !year) return setError("Enter expiry as MM/YY");
      if (!cvv || cvv.length < 3) return setError("Enter a valid CVV");
      if (!cardName.trim()) return setError("Enter the name on the card");
      payload = { method: "card", card: { number: cardDigits, expiry_month: month, expiry_year: year, cvv, name_on_card: cardName } };
    } else if (tab === "upi") {
      if (!/^[\w.-]{2,}@[a-zA-Z]{2,}$/.test(vpa)) return setError("Enter a valid UPI ID, e.g. name@bank");
      payload = { method: "upi", upi: { vpa } };
    } else if (tab === "wallet") {
      if (!wallet) return setError("Choose a wallet");
      payload = { method: "wallet", wallet: { provider: wallet } };
    } else {
      payload = { method: "cod" };
    }

    setProcessing(true);
    try {
      await onSubmit(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment failed");
    } finally {
      setProcessing(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="glass payment-form" style={{ padding: 24 }}>
      <div className="payment-tabs">
        {TABS.map((t) => (
          <button
            type="button"
            key={t.id}
            className={`payment-tab ${tab === t.id ? "active" : ""}`}
            onClick={() => {
              setTab(t.id);
              setError(null);
            }}
          >
            <span className="payment-tab-icon">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "card" && (
        <div className="stack gap-2" style={{ marginTop: 18 }}>
          <div className="field">
            <label>Card number {brand && <span className="card-brand-tag">{brand}</span>}</label>
            <input
              className="input"
              inputMode="numeric"
              placeholder="4242 4242 4242 4242"
              value={cardNumber}
              onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
              maxLength={23}
            />
          </div>
          <div className="field">
            <label>Name on card</label>
            <input className="input" value={cardName} onChange={(e) => setCardName(e.target.value)} placeholder="A. Sharma" />
          </div>
          <div className="field-row">
            <div className="field">
              <label>Expiry (MM/YY)</label>
              <input
                className="input"
                placeholder="12/28"
                maxLength={5}
                value={expiry}
                onChange={(e) => {
                  const digits = e.target.value.replace(/\D/g, "").slice(0, 4);
                  setExpiry(digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits);
                }}
              />
            </div>
            <div className="field">
              <label>CVV</label>
              <input
                className="input"
                inputMode="numeric"
                maxLength={4}
                value={cvv}
                onChange={(e) => setCvv(e.target.value.replace(/\D/g, ""))}
                placeholder="123"
              />
            </div>
          </div>
          <p className="payment-hint">
            Test mode — any Luhn-valid card number works (try <strong>4242 4242 4242 4242</strong>). Numbers ending in{" "}
            <strong>0002</strong> simulate a decline.
          </p>
        </div>
      )}

      {tab === "upi" && (
        <div className="stack gap-2" style={{ marginTop: 18 }}>
          <div className="field">
            <label>UPI ID</label>
            <input className="input" value={vpa} onChange={(e) => setVpa(e.target.value)} placeholder="yourname@upi" />
          </div>
          <p className="payment-hint">
            Test mode — any well-formed UPI ID succeeds. Use <strong>fail@upi</strong> to simulate a decline.
          </p>
        </div>
      )}

      {tab === "wallet" && (
        <div className="wallet-grid" style={{ marginTop: 18 }}>
          {WALLETS.map((w) => (
            <button
              type="button"
              key={w.id}
              className={`wallet-option ${wallet === w.id ? "selected" : ""}`}
              onClick={() => setWallet(w.id)}
            >
              {w.label}
            </button>
          ))}
        </div>
      )}

      {tab === "cod" && (
        <div className="stack gap-2" style={{ marginTop: 18 }}>
          <p className="payment-hint">Pay in cash when your order arrives. Order will be marked pending until delivery.</p>
        </div>
      )}

      {error && <p className="error-text" style={{ marginTop: 14 }}>{error}</p>}
      <button className="btn btn-primary btn-block" type="submit" disabled={processing} style={{ marginTop: 20 }}>
        {processing ? <span className="spinner" /> : tab === "cod" ? `Place order · ${total}` : `Pay ${total}`}
      </button>
      <p className="payment-hint" style={{ marginTop: 12 }}>
        Simulated payment gateway — no real card, bank, or wallet is charged.
      </p>
    </form>
  );
}
