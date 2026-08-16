import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../hooks/useAuth";
import { ApiError } from "../api/types";
import { useToast } from "../components/ui/Toast";
import "./auth.css";

export function RegisterPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { register } = useAuth();
  const { push } = useToast();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register(email, password, fullName);
      push("Account created — welcome to Trove!", "success");
      navigate(params.get("next") ?? "/");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not create account");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="center-page">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="glass auth-card">
        <span className="eyebrow">Join Trove</span>
        <h1 className="auth-title">Create your account</h1>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Full name</label>
            <input className="input" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div className="field">
            <label>Email</label>
            <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="field">
            <label>Password</label>
            <input className="input" type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
            <span style={{ fontSize: 12, color: "var(--text-faint)" }}>At least 8 characters</span>
          </div>
          {error && <p className="error-text" style={{ marginBottom: 14 }}>{error}</p>}
          <button className="btn btn-primary btn-block" type="submit" disabled={loading}>
            {loading ? <span className="spinner" /> : "Create account"}
          </button>
        </form>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </motion.div>
    </div>
  );
}
