"""Guardians: three ways to decide whether to interrupt a payment during a conversation."""
import re

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

KEYWORDS = ["urgent", "act today", "right now", "do not tell", "keep this between", "safe account", "secure account", "new account",
            "security team", "fraud department", "guaranteed", "prize", "install", "share the code", "trust"]


def context(ep):
    return [ep["new_payee"], min(ep["amount"] / max(1, ep["typical"]), 10) / 10]


class KeywordGuardian:
    """Fixed word list, the sort of rule a first version would use."""
    name = "keyword rules"

    def fit(self, eps):
        return self

    def score(self, eps):
        return np.array([sum(k in ep["text"].lower() for k in KEYWORDS) + 0.1 * ep["new_payee"] for ep in eps], float)


class ContextGuardian:
    """Only looks at the payment: new payee and amount compared with the customer's usual."""
    name = "payment context only"

    def fit(self, eps):
        self.m = LogisticRegression(max_iter=500).fit([context(e) for e in eps], [e["label"] for e in eps])
        return self

    def score(self, eps):
        return self.m.predict_proba([context(e) for e in eps])[:, 1]


class TextGuardian:
    """Conversation text (word and phrase patterns) plus payment context."""
    name = "text + context model"

    def fit(self, eps):
        self.v = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        X = self.v.fit_transform([e["text"] for e in eps])
        self.m = LogisticRegression(max_iter=1000, C=3.0).fit(hstack([X, csr_matrix([context(e) for e in eps])]), [e["label"] for e in eps])
        return self

    def score(self, eps):
        X = self.v.transform([e["text"] for e in eps])
        return self.m.predict_proba(hstack([X, csr_matrix([context(e) for e in eps])]))[:, 1]


def threshold_for_fpr(scores, labels, target=0.03):
    neg = np.sort(scores[np.array(labels) == 0])
    k = int(np.ceil((1 - target) * len(neg))) - 1
    return float(neg[min(max(k, 0), len(neg) - 1)]) + 1e-9


def explain(g: "TextGuardian", ep, top=3):
    """Words in the conversation that pushed the score up the most."""
    v = g.v
    x = v.transform([ep["text"]])
    names = v.get_feature_names_out()
    coef = g.m.coef_[0][: len(names)]
    idx = x.nonzero()[1]
    contrib = sorted(((float(coef[i] * x[0, i]), names[i]) for i in idx), reverse=True)
    return [w for c, w in contrib[:top] if c > 0]
