import { useState } from "react";
import type { Review } from "../../api/types";
import { StarRating } from "../ui/StarRating";
import "./reviews.css";

export function ReviewList({ reviews }: { reviews: Review[] }) {
  if (reviews.length === 0) {
    return <p className="review-empty">No reviews yet — be the first to write one.</p>;
  }
  return (
    <div className="review-list">
      {reviews.map((r) => (
        <div key={r.id} className="review-item glass">
          <div className="row gap-1" style={{ justifyContent: "space-between" }}>
            <StarRating value={r.rating} />
            <span className="review-author">{r.reviewer_name}</span>
          </div>
          <h4 className="review-title">{r.title}</h4>
          <p className="review-body">{r.body}</p>
        </div>
      ))}
    </div>
  );
}

export function ReviewForm({
  onSubmit,
  submitting,
}: {
  onSubmit: (rating: number, title: string, body: string) => Promise<void> | void;
  submitting?: boolean;
}) {
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !body.trim()) return;
    await onSubmit(rating, title.trim(), body.trim());
    setTitle("");
    setBody("");
    setRating(5);
  }

  return (
    <form className="review-form glass" onSubmit={handleSubmit}>
      <div className="field">
        <label>Your rating</label>
        <StarRating value={rating} interactive onChange={setRating} size={22} />
      </div>
      <div className="field">
        <label>Title</label>
        <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Summarize your experience" maxLength={255} required />
      </div>
      <div className="field">
        <label>Review</label>
        <textarea
          className="input"
          rows={4}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="What did you like or dislike?"
          required
        />
      </div>
      <button className="btn btn-primary" type="submit" disabled={submitting}>
        {submitting ? <span className="spinner" /> : "Submit review"}
      </button>
    </form>
  );
}
