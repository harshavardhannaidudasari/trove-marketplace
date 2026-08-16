import { useState, type FormEvent } from "react";
import type { AddressInput } from "../../api/types";

const EMPTY: AddressInput = {
  line1: "",
  line2: "",
  city: "",
  state: "",
  postal_code: "",
  country: "US",
  is_default: true,
};

export function AddressForm({
  onSubmit,
  submitting,
  onCancel,
}: {
  onSubmit: (address: AddressInput) => void;
  submitting?: boolean;
  onCancel?: () => void;
}) {
  const [form, setForm] = useState<AddressInput>(EMPTY);

  function set<K extends keyof AddressInput>(key: K, value: AddressInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit(form);
  }

  return (
    <form className="glass address-form" onSubmit={handleSubmit} style={{ padding: 24 }}>
      <div className="field">
        <label>Address line 1</label>
        <input className="input" required value={form.line1} onChange={(e) => set("line1", e.target.value)} placeholder="123 Market Street" />
      </div>
      <div className="field">
        <label>Address line 2 (optional)</label>
        <input className="input" value={form.line2 ?? ""} onChange={(e) => set("line2", e.target.value)} placeholder="Apt, suite, etc." />
      </div>
      <div className="field-row">
        <div className="field">
          <label>City</label>
          <input className="input" required value={form.city} onChange={(e) => set("city", e.target.value)} />
        </div>
        <div className="field">
          <label>State</label>
          <input className="input" required value={form.state} onChange={(e) => set("state", e.target.value)} />
        </div>
      </div>
      <div className="field-row">
        <div className="field">
          <label>Postal code</label>
          <input className="input" required value={form.postal_code} onChange={(e) => set("postal_code", e.target.value)} />
        </div>
        <div className="field">
          <label>Country</label>
          <input
            className="input"
            required
            maxLength={2}
            value={form.country}
            onChange={(e) => set("country", e.target.value.toUpperCase())}
          />
        </div>
      </div>
      <div className="row gap-2" style={{ marginTop: 8 }}>
        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? <span className="spinner" /> : "Save address"}
        </button>
        {onCancel && (
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
