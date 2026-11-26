import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle2,
  ChevronRight,
  Gift,
  History,
  Ticket,
} from "lucide-react";
import { useSoilSync } from "../state";
import { Dialog } from "../components/UI";
import { figma } from "../data/figma";
import { rewardAvailability } from "../model";
import { DailyCheckin } from "./Home";
import vindaTissue from "../assets/reward-products/vinda-tissue.jpg";
import vindaKitchenPaper from "../assets/reward-products/vinda-kitchen-paper.jpg";
import petpetDiapers from "../assets/reward-products/petpet-diapers.png";

const productPhotos = {
  "vinda-tissue": vindaTissue,
  "vinda-kitchen-paper": vindaKitchenPaper,
  "petpet-diapers": petpetDiapers,
};
const featured = ["coffee-cup", "coffee-beans", "coffee-grounds", ...Object.keys(productPhotos)];

export function rewardPhoto(reward, index = 0) {
  if (Object.hasOwn(productPhotos, reward?.id)) return productPhotos[reward.id];
  return figma.rewards[
    {
      nursery: 0,
      market: 1,
      composter: 2,
      seeds: 0,
      bag: 1,
      coffee: 0,
      "coffee-beans": 1,
      "coffee-grounds": 2,
    }[reward?.kind] ?? index % 3
  ].src;
}

export default function Rewards() {
  const { state, act, busy, setNotice } = useSoilSync();
  const [confirm, setConfirm] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [receipt, setReceipt] = useState(null);
  const rewards = state.catalog.rewards
    .filter((row) => row.active !== false)
    .sort((a, b) => {
      const rank = (reward) =>
        featured.includes(reward.id)
          ? featured.indexOf(reward.id)
          : featured.length;
      return rank(a) - rank(b);
    });
  const collapsedCount = Math.max(3, rewards.filter((reward) => featured.includes(reward.id)).length);
  async function redeem() {
    if (!confirm || busy) return;
    const result = await act({
      type: "REDEEM",
      id: crypto.randomUUID(),
      rewardId: confirm.id,
    });
    if (result) {
      setReceipt({ ...result, reward: confirm });
      setConfirm(null);
      setNotice(
        `Redeemed: ${confirm.name} (−${result.cost ?? confirm.cost} pts)`,
      );
    }
  }
  return (
    <div className="page-stack rewards-page final-rewards">
      <div className="rewards-wallet">
        <Ticket size={17} />
        <span>{state.balance.toLocaleString()} points available</span>
      </div>
      <DailyCheckin reward />
      <div className="reward-section-tabs">
        <span className="badge">Available</span>
        <Link to="/rewards/history">
          <History size={13} /> Redemption History
        </Link>
      </div>
      <div className="section-heading">
        <h2>Catalog rewards</h2>
        <small>Tap to exchange</small>
      </div>
      <div className="reward-catalog">
        {rewards.slice(0, expanded ? undefined : collapsedCount).map((reward, index) => {
          const unavailable = rewardAvailability(state, reward);
          const hasProductPhoto = Object.hasOwn(productPhotos, reward.id);
          return (
            <button
              className={hasProductPhoto ? "catalog-reward household-reward" : "catalog-reward"}
              key={reward.id}
              disabled={Boolean(unavailable) || busy}
              aria-label={`Redeem ${reward.name} for ${reward.cost} points${unavailable ? `: ${unavailable}` : ""}`}
              aria-describedby={`reward-description-${reward.id}`}
              onClick={() => setConfirm(reward)}
            >
              <img src={rewardPhoto(reward, index)} alt="" />
              <span className="catalog-reward-copy">
                <strong>{reward.name}</strong>
                <small id={`reward-description-${reward.id}`}>{reward.description}</small>
              </span>
              <span className="catalog-reward-price">
                <strong>
                  {reward.cost} <small>pts</small>
                </strong>
                <small>
                  {unavailable === "Already claimed"
                    ? "Claimed"
                    : unavailable
                      ? "Earn more pts"
                      : "Tap to claim"}
                </small>
              </span>
            </button>
          );
        })}
      </div>
      {rewards.length > collapsedCount && (
        <button
          type="button"
          className="text-button more-rewards"
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
        >
          {expanded
            ? "Show fewer rewards"
            : `View all ${rewards.length} rewards`}
        </button>
      )}
      <p className="concept-note">
        Project reward concepts. Collection and partner fulfilment to be
        confirmed.
      </p>
      {confirm && (
        <Dialog title="Redeem this reward?" onClose={() => setConfirm(null)}>
          <img
            className={Object.hasOwn(productPhotos, confirm.id) ? "reward-dialog-photo product-photo" : "reward-dialog-photo"}
            src={rewardPhoto(confirm)}
            alt=""
          />
          <h3>{confirm.name}</h3>
          <p>
            {confirm.cost} EcoPoints will be deducted from your balance. This is
            a project reward concept.
          </p>
          <button className="button" disabled={busy} onClick={redeem}>
            {busy ? "Saving claim…" : `Confirm · ${confirm.cost} pts`}
          </button>
          <button
            className="text-button cancel-button"
            onClick={() => setConfirm(null)}
          >
            Keep browsing
          </button>
        </Dialog>
      )}
      {receipt && (
        <Dialog title="Redemption recorded" onClose={() => setReceipt(null)}>
          <CheckCircle2 size={36} />
          <h3>{receipt.reward.name}</h3>
          <p>{receipt.cost} points exchanged.</p>
          <p className="claim-code">{receipt.claimCode}</p>
          <p className="concept-note">
            Keep this claim reference. Partner collection is not yet connected.
          </p>
          <Link className="button" to="/rewards/history">
            View redemption history <ChevronRight size={17} />
          </Link>
        </Dialog>
      )}
    </div>
  );
}

export function RedemptionHistory() {
  const { state } = useSoilSync();
  const [receipt, setReceipt] = useState(null);
  const claims = [...state.redemptions].sort(
    (a, b) => new Date(b.at) - new Date(a.at),
  );
  return (
    <div className="page-stack redemption-page">
      {!claims.length && (
        <section className="empty-card">
          <Gift size={32} />
          <h2>Your next little reward</h2>
          <p>Rewards you claim will appear here.</p>
          <Link to="/rewards" className="button">
            Browse rewards
          </Link>
        </section>
      )}
      {claims.map((claim, index) => {
        const reward = state.catalog.rewards.find(
          (row) => row.id === claim.rewardId,
        );
        return (
          <button
            className="redemption-card"
            key={claim.id}
            onClick={() => setReceipt({ ...claim, reward })}
          >
            <span className="row-between">
              <time dateTime={claim.at}>
                {new Date(claim.at).toLocaleString("en-MY", {
                  month: "short",
                  day: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </time>
              <span className="badge">−{claim.cost} pts</span>
            </span>
            <span className="redemption-card-body">
              <img src={rewardPhoto(reward, index)} alt="" />
              <span>
                <strong>{reward?.name || "Reward claim"}</strong>
                <small>
                  {reward?.displayCategory || "SoilSync partner concept"}
                </small>
                <small>
                  {claim.expiresAt
                    ? `Valid until ${new Date(claim.expiresAt).toLocaleDateString("en-MY")}`
                    : "Collection details to be confirmed"}
                </small>
              </span>
            </span>
          </button>
        );
      })}
      {receipt && (
        <Dialog title="Your redemption" onClose={() => setReceipt(null)}>
          <h3>{receipt.reward?.name || "Reward claim"}</h3>
          <p className="claim-code">{receipt.claimCode}</p>
          <p>{receipt.cost} points exchanged.</p>
          <p className="concept-note">
            This reference records your project claim. It is not a live partner
            voucher.
          </p>
          <button className="button" onClick={() => setReceipt(null)}>
            Done
          </button>
        </Dialog>
      )}
    </div>
  );
}
