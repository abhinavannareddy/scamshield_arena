"""Synthetic, generic conversation generator for scam-defence testing.

All text is invented and deliberately generic: it contains the well-known warning signs of scams (urgency, secrecy,
pressure to move money) and nothing operational. No real names, brands, phone numbers or account details."""
import random

# tactic -> phrase variants. A = common wording, B = paraphrases a scammer might switch to once A is caught,
# C = a second paraphrase set that the guardian never trains on (held out).
TACTICS = {
    "urgency": {
        "A": ["You must act today or you will lose access.", "This is urgent, it cannot wait.", "You need to do this right now."],
        "B": ["Time is very short here, the window closes soon.", "We have only a few minutes left to fix this.", "Please move quickly, delays make it worse."],
        "C": ["Every minute counts, so let us finish this immediately.", "The deadline is almost over for this matter.", "Waiting even an hour could be costly."],
    },
    "secrecy": {
        "A": ["Do not tell anyone about this call.", "Keep this between us, please.", "Do not mention this to your bank or family."],
        "B": ["It is best if nobody else hears about this.", "Please handle this privately, without involving others.", "Others may not understand, so no need to share."],
        "C": ["This stays confidential, just the two of us.", "Talking to other people would only complicate things.", "Let us keep the circle small on this one."],
    },
    "authority": {
        "A": ["I am calling from the security team.", "This is the fraud department speaking.", "I work for the official support office."],
        "B": ["I represent the team that protects your savings.", "My unit looks after account safety.", "I am an officer handling your case."],
        "C": ["I am part of the protection group assigned to you.", "Our compliance desk opened a file on your name.", "I am the senior contact for your profile."],
    },
    "move_money": {
        "A": ["Transfer your money to a safe account now.", "Send the payment to the new account I give you.", "Move your savings to this secure account."],
        "B": ["Shift the funds over to the holding account for protection.", "Pay the amount into the account I will share.", "Place your balance in the temporary account."],
        "C": ["Relocate the balance to the custody account today.", "Wire the sum to the reference account provided.", "Put the funds into the escrow-style account I name."],
    },
    "too_good": {
        "A": ["This investment pays guaranteed high returns.", "You have won a prize, only a small fee is needed.", "Double your money with no risk."],
        "B": ["Members here see steady gains every single week.", "A reward is waiting for you after a small handling charge.", "Our clients never lose on this plan."],
        "C": ["The returns on this are simply remarkable and safe.", "Your bonus is reserved once the processing cost is paid.", "There is no downside to joining early."],
    },
    "emotional": {
        "A": ["I really care about you and need your help.", "I am in trouble and you are the only one I trust.", "Please help me, I have nobody else."],
        "B": ["You mean so much to me and I feel stuck.", "I hate to ask, but my situation is serious.", "I only feel safe talking with you."],
        "C": ["It would break my heart if you said no.", "You are my last hope with this problem.", "I would never ask unless it truly mattered."],
    },
    "remote_access": {
        "A": ["Please install the support app so I can see your screen.", "Share the code we send you so I can verify you."],
        "B": ["Let me connect to your device to fix the issue.", "Read me the number you receive so we can continue."],
        "C": ["Open the helper tool and let me guide you from my side.", "Tell me the digits on your phone to confirm it is you."],
    },
}

SCAM_TYPES = {  # which tactics each scam type tends to use (core, optional)
    "bank_impersonation": (["authority", "urgency", "move_money"], ["secrecy", "remote_access"]),
    "investment": (["too_good", "move_money"], ["urgency", "emotional"]),
    "romance": (["emotional", "move_money"], ["secrecy", "urgency"]),
    "invoice_redirect": (["authority", "move_money"], ["urgency"]),
    "tech_support": (["authority", "remote_access"], ["urgency", "move_money", "secrecy"]),  # held out from training
}
SEEN_TYPES = ["bank_impersonation", "investment", "romance", "invoice_redirect"]
HELD_OUT_TYPES = ["tech_support"]

# legitimate situations, including hard negatives that reuse warning-sign words in an innocent way
LEGIT = {
    "rent": (["Rent is due today, can you send it?", "Sending the rent now, thanks."], 0.3),
    "family": (["Can you send me some money for the trip?", "Here is the amount we talked about."], 0.4),
    "supplier": (["The invoice is attached, payment is due this week.", "Please confirm the invoice number before paying."], 0.2),
    "surprise_gift": (["Keep it secret, it is a surprise party.", "Do not tell her, the gift is for her birthday."], 0.4),
    "bank_notice": (["This is your bank letting you know about a new card. No action is needed.", "We are calling to confirm a payment you made. Nothing is wrong."], 0.1),
    "urgent_real": (["I need this paid urgently, the deadline is today.", "It is urgent, the school fee is due now."], 0.3),
    "second_hand": (["Is the item still available? I can pay on pickup.", "I will send the money after I see it."], 0.3),
}

PERSONAS = {  # style and payment behaviour (synthetic)
    "older_cautious": {"prefix": ["Hello, thank you very much for your message. ", "Good day. I would like to understand this properly. "], "typical": 5000, "new_payee": 0.15, "legit_mix": ["rent", "family", "bank_notice", "surprise_gift"]},
    "young_busy": {"prefix": ["hey ", "ok so ", "quick one: "], "typical": 1500, "new_payee": 0.5, "legit_mix": ["rent", "family", "second_hand", "surprise_gift", "urgent_real"]},
    "small_business": {"prefix": ["Regarding the order: ", "Hi, following up: "], "typical": 20000, "new_payee": 0.35, "legit_mix": ["supplier", "urgent_real", "bank_notice", "rent"]},
    "new_to_country": {"prefix": ["Please, I need help. ", "I am not sure the words. ", "Sorry my language is small. "], "typical": 3000, "new_payee": 0.45, "legit_mix": ["rent", "family", "urgent_real", "bank_notice", "surprise_gift"]},
}

SUBTLE_SCAM, HARD_NEGATIVE = 0.3, 0.3

FILLER = ["Okay.", "I see.", "Let me think.", "Can you explain?", "Yes.", "Thank you.", "Understood."]


def make_episode(rng: random.Random, persona: str, scam_type: str | None, variant: str = "A", ep_id: int = 0) -> dict:
    p = PERSONAS[persona]
    turns = []
    if scam_type:
        core, opt = SCAM_TYPES[scam_type]
        tactics = list(core) + [t for t in opt if rng.random() < 0.5]
        if rng.random() < SUBTLE_SCAM:  # a subtle scam shows only one warning sign
            tactics = [rng.choice(core)]
        rng.shuffle(tactics)
        for t in tactics:
            bank = TACTICS[t][variant if variant in TACTICS[t] else "A"]
            turns.append(("other", rng.choice(bank)))
            turns.append(("customer", p["prefix"][rng.randrange(len(p["prefix"]))] + rng.choice(FILLER)))
        for _ in range(rng.randint(0, 2)):  # scammers borrow ordinary-sounding cover phrases
            turns.insert(rng.randrange(len(turns) + 1), ("other", rng.choice(LEGIT[rng.choice(list(LEGIT))][0])))
        amount = max(200, rng.gauss(p["typical"] * 3, p["typical"]))
        new_payee, label = True if rng.random() < 0.9 else False, 1
        kind = scam_type
    else:
        kind = rng.choice(p["legit_mix"])
        phrases, new_p = LEGIT[kind]
        for _ in range(rng.randint(1, 3)):
            turns.append(("other", rng.choice(phrases)))
            turns.append(("customer", p["prefix"][rng.randrange(len(p["prefix"]))] + rng.choice(FILLER)))
        if rng.random() < HARD_NEGATIVE:  # innocent conversation that also contains a warning-sign phrase
            t = rng.choice(["urgency", "secrecy", "emotional", "authority", "move_money"])
            turns.insert(rng.randrange(len(turns) + 1), ("other", rng.choice(TACTICS[t][variant if variant in TACTICS[t] else "A"])))
        amount = max(50, rng.gauss(p["typical"], p["typical"] * 0.5))
        new_payee, label = rng.random() < max(new_p, p["new_payee"] * 0.6), 0
    return {"id": ep_id, "persona": persona, "kind": kind, "label": label, "variant": variant, "turns": turns,
            "text": " ".join(t for _, t in turns), "amount": round(amount), "typical": p["typical"], "new_payee": int(new_payee)}


def make_dataset(seed: int, n: int = 800, scam_rate: float = 0.4, scam_types=None, variant="A") -> list:
    rng = random.Random(seed)
    scam_types = scam_types or SEEN_TYPES
    eps = []
    for i in range(n):
        persona = rng.choice(list(PERSONAS))
        st = rng.choice(scam_types) if rng.random() < scam_rate else None
        eps.append(make_episode(rng, persona, st, variant, i))
    return eps
