"""
UGC Helper — Assistant de création de compte
Fenêtre flottante pour assister la création manuelle de comptes UGC.
"""

import os
import random
import string
import tkinter as tk
from tkinter import messagebox
import threading
import time
import webbrowser
import base64
import re
import traceback

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
POLL_INTERVAL_MS = 3000  # 3 seconds — fast but stable
MAX_EMAIL_LENGTH = 50


class UGCHelperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UGC Helper")
        self.root.geometry("380x360")
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        # Paths
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.emails_file = os.path.join(self.cwd, "emails.txt")
        self.results_file = os.path.join(self.cwd, "resultats.txt")
        self.credentials_file = os.path.join(self.cwd, "credentials.json")
        self.token_file = os.path.join(self.cwd, "token.json")

        # State
        self.emails: list[str] = []
        self.used_emails: set[str] = set()
        self.current_index = -1
        self.current_email = ""
        self.current_password = ""
        self.ugc_link: str | None = None
        self.gmail_service = None
        self.gmail_ready = False
        self._poll_scheduled = False

        self._setup_ui()
        self._load_data()
        self._next_account()

        # Gmail init in background
        threading.Thread(target=self._init_gmail, daemon=True).start()

    # ═══════════════════════════════════════
    #  UI
    # ═══════════════════════════════════════
    def _setup_ui(self):
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        accent = "#89b4fa"
        green = "#a6e3a1"
        pink = "#f38ba8"
        muted = "#6c7086"
        font_sm = ("Segoe UI", 9)
        font_md = ("Segoe UI", 11, "bold")
        font_btn = ("Segoe UI", 10, "bold")

        # — Progress —
        self.lbl_progress = tk.Label(self.root, text="—", bg=bg, fg=muted, font=font_sm)
        self.lbl_progress.pack(pady=(12, 0))

        # — Email —
        self.lbl_email = tk.Label(self.root, text="...", bg=bg, fg=fg, font=font_md, wraplength=340)
        self.lbl_email.pack(pady=(4, 2))

        self.btn_email = tk.Button(self.root, text="📋 Copier Email", font=font_btn,
                                   bg=accent, fg="#1e1e2e", activebackground="#74c7ec",
                                   bd=0, cursor="hand2", command=self._copy_email)
        self.btn_email.pack(fill=tk.X, padx=24, ipady=3)

        # — Password —
        self.lbl_pwd = tk.Label(self.root, text="...", bg=bg, fg=fg, font=font_md)
        self.lbl_pwd.pack(pady=(12, 2))

        self.btn_pwd = tk.Button(self.root, text="📋 Copier MDP", font=font_btn,
                                 bg=accent, fg="#1e1e2e", activebackground="#74c7ec",
                                 bd=0, cursor="hand2", command=self._copy_password)
        self.btn_pwd.pack(fill=tk.X, padx=24, ipady=3)

        # — UGC Link —
        self.btn_link = tk.Button(self.root, text="🔗 Lien UGC (en attente...)", font=font_btn,
                                  bg="#45475a", fg=muted, bd=0, state=tk.DISABLED,
                                  command=self._open_link)
        self.btn_link.pack(fill=tk.X, padx=24, pady=(16, 0), ipady=4)

        # — Status label —
        self.lbl_status = tk.Label(self.root, text="⏳ Connexion Gmail...", bg=bg, fg=muted, font=font_sm)
        self.lbl_status.pack(pady=(4, 0))

        # — Next —
        self.btn_next = tk.Button(self.root, text="✅ Suivant (Sauvegarder & Reset)", font=font_btn,
                                  bg=green, fg="#1e1e2e", activebackground="#94e2d5",
                                  bd=0, cursor="hand2", command=self._save_and_next)
        self.btn_next.pack(fill=tk.X, padx=24, pady=(16, 12), ipady=5)

    # ═══════════════════════════════════════
    #  DATA
    # ═══════════════════════════════════════
    def _load_data(self):
        # Load already-done emails
        if os.path.exists(self.results_file):
            with open(self.results_file, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        self.used_emails.add(line.split(":")[0].strip())

        # Load email list (max 50 chars)
        if os.path.exists(self.emails_file):
            with open(self.emails_file, "r", encoding="utf-8") as f:
                self.emails = [
                    l.strip() for l in f
                    if l.strip() and "@" in l and len(l.strip()) <= MAX_EMAIL_LENGTH
                ]
            print(f"[INFO] {len(self.emails)} emails chargés (≤{MAX_EMAIL_LENGTH} chars)")
        else:
            messagebox.showwarning("Fichier manquant", f"{self.emails_file} introuvable")

    @staticmethod
    def _gen_password(length=14) -> str:
        parts = [
            random.choice(string.ascii_lowercase),
            random.choice(string.ascii_uppercase),
            random.choice(string.digits),
            random.choice("!@#$%&*?"),
        ]
        parts += random.choices(string.ascii_letters + string.digits + "!@#$%&*?", k=length - 4)
        random.shuffle(parts)
        return "".join(parts)

    def _next_account(self):
        for i in range(self.current_index + 1, len(self.emails)):
            if self.emails[i] not in self.used_emails:
                self.current_index = i
                self.current_email = self.emails[i]
                self.current_password = self._gen_password()
                self.ugc_link = None

                # UI updates
                self.lbl_progress.config(text=f"Email {i + 1} / {len(self.emails)}")
                display = self.current_email if len(self.current_email) < 35 else self.current_email[:32] + "..."
                self.lbl_email.config(text=display)
                self.lbl_pwd.config(text=self.current_password)
                self.btn_link.config(text="🔗 Lien UGC (en attente...)", bg="#45475a", fg="#6c7086", state=tk.DISABLED)
                self.lbl_status.config(text="⏳ En attente du mail UGC...")

                # Mark old emails as read for this alias (background)
                if self.gmail_ready:
                    threading.Thread(target=self._mark_old_read, args=(self.current_email,), daemon=True).start()
                return

        self.lbl_email.config(text="🎉 Plus d'emails disponibles !")
        self.lbl_pwd.config(text="—")

    # ═══════════════════════════════════════
    #  CLIPBOARD
    # ═══════════════════════════════════════
    def _copy_email(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_email)
        self.root.update()

    def _copy_password(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_password)
        self.root.update()

    def _open_link(self):
        if self.ugc_link:
            webbrowser.open(self.ugc_link)
            self.btn_link.config(text="🔗 Lien ouvert ✓", bg="#45475a", fg="#a6e3a1")

    def _save_and_next(self):
        if self.current_email:
            with open(self.results_file, "a", encoding="utf-8") as f:
                f.write(f"{self.current_email}:{self.current_password}\n")
            self.used_emails.add(self.current_email)
            self._next_account()

    # ═══════════════════════════════════════
    #  GMAIL API
    # ═══════════════════════════════════════
    def _init_gmail(self):
        try:
            creds = None
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        self.root.after(0, lambda: messagebox.showerror(
                            "Credentials manquants",
                            f"Placez credentials.json dans:\n{self.cwd}\n\nVoir setup_gmail.md"
                        ))
                        return
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)

                with open(self.token_file, 'w') as f:
                    f.write(creds.to_json())

            self.gmail_service = build('gmail', 'v1', credentials=creds)
            self.gmail_ready = True
            print("[INFO] Gmail API connectée ✅")
            self.root.after(0, lambda: self.lbl_status.config(text="✅ Gmail connecté — polling actif"))

            # Mark old emails as read for current alias
            if self.current_email:
                self._mark_old_read(self.current_email)

            # Start polling on the main thread via after()
            self.root.after(1000, self._poll)

        except Exception as e:
            print(f"[ERROR] Gmail init failed: {e}")
            traceback.print_exc()
            self.root.after(0, lambda: self.lbl_status.config(text=f"❌ Gmail: {str(e)[:40]}"))

    def _mark_old_read(self, email_alias: str):
        """Mark any existing unread UGC emails for this alias as read."""
        if not self.gmail_service:
            return
        try:
            query = f'is:unread "{email_alias}" ugc'
            results = self.gmail_service.users().messages().list(
                userId='me', q=query, includeSpamTrash=True
            ).execute()
            messages = results.get('messages', [])
            if messages:
                ids = [m['id'] for m in messages]
                self.gmail_service.users().messages().batchModify(
                    userId='me', body={'ids': ids, 'removeLabelIds': ['UNREAD']}
                ).execute()
                print(f"[CLEAN] {len(ids)} anciens emails marqués comme lus pour {email_alias}")
        except Exception as e:
            print(f"[CLEAN-WARN] Nettoyage échoué (non bloquant): {e}")

    def _poll(self):
        """Poll Gmail for activation email. Runs on main thread via root.after()."""
        if not self.gmail_ready or not self.current_email or self.ugc_link is not None:
            self.root.after(POLL_INTERVAL_MS, self._poll)
            return

        try:
            query = f'is:unread "{self.current_email}" ugc'
            results = self.gmail_service.users().messages().list(
                userId='me', q=query, maxResults=5, includeSpamTrash=True
            ).execute()
            messages = results.get('messages', [])

            if messages:
                for entry in messages:
                    try:
                        link = self._extract_activation_link(entry['id'])
                        if link:
                            self.ugc_link = link
                            print(f"[FOUND] ✅ Lien UGC: {link[:80]}...")
                            self.btn_link.config(
                                text="🔗 LIEN UGC TROUVÉ !",
                                bg="#f38ba8", fg="#1e1e2e",
                                state=tk.NORMAL
                            )
                            self.lbl_status.config(text="✅ Lien trouvé ! Clique dessus.")
                            break
                    except Exception as e:
                        print(f"[WARN] Erreur extraction msg {entry['id']}: {e}")

        except Exception as e:
            # Network / SSL / API errors — just log and retry next cycle
            print(f"[POLL-ERR] {e}")

        # Always reschedule
        self.root.after(POLL_INTERVAL_MS, self._poll)

    def _extract_activation_link(self, msg_id: str) -> str | None:
        """Fetch a message and extract the UGC activation link."""
        msg = self.gmail_service.users().messages().get(
            userId='me', id=msg_id, format='full'
        ).execute()

        # Get body HTML
        payload = msg.get('payload', {})
        body_data = self._get_html_body(payload)
        if not body_data:
            return None

        html = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')

        # Find all Mailjet tracking links and decode their destination
        all_links = re.findall(r'href="(https?://[a-zA-Z0-9._-]+\.mjt\.lu/lnk/[^"]*)"', html, re.IGNORECASE)
        for link in all_links:
            try:
                last_part = link.split('/')[-1]
                padded = last_part + '=' * (-len(last_part) % 4)
                decoded = base64.urlsafe_b64decode(padded).decode('utf-8', errors='ignore')
                if 'activation' in decoded.lower() or 'moncompteinscription' in decoded.lower():
                    return link
            except Exception:
                continue

        # Fallback: direct UGC links
        match = re.search(r'href="(https://[^"]*ugc\.fr[^"]*activation[^"]*)"', html, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def _get_html_body(payload: dict) -> str | None:
        """Recursively extract text/html body data from a Gmail message payload."""
        parts = payload.get('parts', [])
        if parts:
            for part in parts:
                if part.get('mimeType') == 'text/html' and part.get('body', {}).get('data'):
                    return part['body']['data']
                # Recurse into nested parts
                if part.get('parts'):
                    result = UGCHelperApp._get_html_body(part)
                    if result:
                        return result
            # Fallback to text/plain
            for part in parts:
                if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                    return part['body']['data']
        else:
            return payload.get('body', {}).get('data')
        return None


if __name__ == "__main__":
    root = tk.Tk()
    app = UGCHelperApp(root)
    root.mainloop()
