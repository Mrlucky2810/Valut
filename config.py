import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGODB_URL = os.getenv('MONGODB_URL')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'minati_bot')
CUSTOMER_CARE_USERNAME = os.getenv('CUSTOMER_CARE_USERNAME')

# Social Media Links
SOCIAL_LINKS = {
    'twitter': 'https://x.com/minatifi?t=wD6ywZfQ1fRdAvHW7x2Txw&s=08',
    'instagram': 'https://www.instagram.com/minativerse_edtech?igsh=MXE4cWx5ZjZydzUxZg==    ',
    'telegram': 'https://t.me/mntchkk',
    'app_download': 'https://play.google.com/store/apps/details?id=com.app.minati_wallet',
}

# Bot messages
WELCOME_MESSAGE = """
🚀 Welcome to Minati Vault Bot!

To complete the process, follow these steps:
1️⃣ Download vault and review
2️⃣ Follow us on Twitter (X)
3️⃣ Follow us on Instagram  
4️⃣ Join our Telegram channel
5️⃣ Send your Minati Vault BEP20 address
6️⃣ Submit final verification

Let's start! 🎯
"""

STEPS = {
    1: "📥 Please download and review the Minati Vault app first.\n\n🔗 **Download Link:** [Minati Vault App](https://play.google.com/store/apps/details?id=com.app.minati_wallet)\n\nAfter downloading and reviewing, click the button below.",
    2: "🐦 **Twitter (X) Tasks:**\n\n1. Follow us: [Follow @MinatiVault](https://x.com/minatifi?t=wD6ywZfQ1fRdAvHW7x2Txw&s=08)\n2. Like our latest post\n3. Retweet with comment\n\n📝 **Send your Twitter username** (without @) after completing all tasks.",
    3: "📸 **Instagram Tasks:**\n\n1. Follow us: [Follow @MinatiVault](https://www.instagram.com/minativerse_edtech?igsh=MXE4cWx5ZjZydzUxZg==)\n2. Like our latest post\n3. Share to your story (optional)\n\n📝 **Send your Instagram username** (without @) after completing all tasks.",
    4: "💬 **Telegram Tasks:**\n\n1. Join our channel: [Join MinatiVault Channel](https://t.me/mntckk)\n2. Share the channel with friends\n\n✅ Click the button below after joining.",
    5: "🏦 **BEP20 Address Submission:**\n\nPlease send your Minati Vault BEP20 address for rewards.\n\n⚠️ **Important:** Make sure it's a valid BEP20 address starting with 0x",
    6: "🎉 **Final Verification:**\n\nReview your information and confirm all tasks are completed.\n\n📞 **Customer Care:** Contact @{} for any issues."
}