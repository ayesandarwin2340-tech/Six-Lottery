import telebot
import requests
import time
import os
from threading import Thread
from flask import Flask

# ===== WEB SERVER FOR RENDER =====
app = Flask('')

@app.route('/')
def home():
    return "🔥 Bot is Online and Dominating!"

def run_web_server():
    # Render အတွက် Port 10000 ကို Default ထားပါတယ်
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ===== BOT CONFIG =====
# Token များကို ဤနေရာတွင် လုံခြုံစွာထားပါ
API_TOKEN = '8543711757:AAGY_Lw3CxurpqQ8SVdAF93EtJfPUJyM0wc'
MY_CHAT_ID = '-1002756417115'
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzY2NjgwNzM4IiwibmJmIjoiMTc2NjY4MDczOCIsImV4cCI6IjE3NjY2ODI1MzgiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIxMi8yNS8yMDI1IDExOjM4OjU4IFBNIiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9yb2xlIjoiQWNjZXNzX1Rva2VuIiwiVXNlcklkIjoiMTA2OTM4MCIsIlVzZXJOYW1lIjoiOTU5MjU0MjE3NTEwIiwiVXNlclBob3RvIjoiNiIsIk5pY2tOYW1lIjoiTWVtYmVyTk5HWVdKRlEiLCJBbW91bnQiOiI0Njc0Ljg0IiwiSW50ZWdyYWwiOiIwIiwiTG9naW5NYXJrIjoiSDUiLCJMb2dpblRpbWUiOiIxMi8yNS8yMDI1IDExOjA4OjU4IFBNIiwiTG9naW5JUEFkZHJlc3MiOiIxMDQuMjM0LjIzMy4yIiwiRGJOdW1iZXIiOiIwIiwiSXN2YWxpZGF0b3IiOiIwIiwiS2V5Q29kZSI6IjI0OSIsIlRva2VuVHlwZSI6IkFjY2Vzc19Ub2tlbiIsIlBob25lVHlwZSI6IjEiLCJVc2VyVHlwZSI6IjAiLCJVc2VyTmFtZTIiOiIiLCJpc3MiOiJqd3RJc3N1ZXIiLCJhdWQiOiJsb3R0ZXJ5VGlja2V0In0.zPTjzgalcipTiSJPV8AS5kTAiAoUkt9XBgSuU23CQrg" # Token အပြည့်အစုံပြန်ထည့်ရန်
GAME_RESULT_URL = "https://6lotteryapi.com/api/webapi/GetNoaverageEmerdList"

bot = telebot.TeleBot(API_TOKEN)
LAST_PREDICTED_ISSUE = None
LAST_PREDICTION_SIZE = None
LAST_PREDICTION_COLOR = None

# Stats Tracking
history_list = []
total_win = 0
total_lose = 0
current_win_streak = 0
max_win_streak = 0
current_lose_streak = 0
max_lose_streak = 0

# ================= HELPERS =================
def get_size(num):
    return "SMALL" if int(num) <= 4 else "BIG"

def get_color(num):
    n = int(num)
    if n in [0, 5]:
        return "VIOLET"
    elif n % 2 == 0:
        return "RED"
    else:
        return "GREEN"

def fetch_data():
    try:
        payload = {
            "pageSize": 10,
            "pageNo": 1,
            "typeId": 30,
            "language": 7,
            "random": "386d58c5bc0e4b24897d7d05c962ab4d",
            "signature": "6CEC36CF4250FC3E925818BDF45481BA",
            "timestamp": int(time.time())
        }
        headers = {
            "Content-Type": "application/json;charset=UTF-8", 
            "Authorization": AUTH_TOKEN,
            "User-Agent": "Mozilla/5.0" # ပိုစိတ်ချရအောင် ထည့်ပေးထားသည်
        }
        r = requests.post(GAME_RESULT_URL, json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("data", {}).get("list", [])
        return []
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

# ================= PREDICTION LOGIC =================
def pro_predict(results):
    if not results or len(results) < 5:
        return "BIG", "RED", 50, 50

    sizes = [get_size(x["number"]) for x in results]
    colors = [get_color(x["number"]) for x in results]
    
    # ရိုးရှင်းသော အခြေခံ Logic (သင့်မူရင်းကို အခြေခံသည်)
    recent_sizes = sizes[:5]
    if recent_sizes.count("BIG") >= 4:
        pred_size, size_conf = "SMALL", 85
    elif recent_sizes.count("SMALL") >= 4:
        pred_size, size_conf = "BIG", 85
    else:
        pred_size, size_conf = ("BIG" if sizes[0] == "SMALL" else "SMALL"), 65

    # Color Logic
    if colors.count("RED") >= 3:
        pred_color, color_conf = "GREEN", 80
    else:
        pred_color, color_conf = "RED", 80

    return pred_size, pred_color, size_conf, color_conf

# ================= STATS DISPLAY =================
def send_summary():
    global history_list, total_win, total_lose, max_win_streak, max_lose_streak
    if not history_list: return

    total_games = total_win + total_lose
    win_rate = (total_win / total_games * 100) if total_games > 0 else 0
    
    table_rows = ""
    for h in reversed(history_list):
        table_rows += f"`{h['issue'][-3:]} | {h['pred_size'][0]}->{h['actual_size'][0]} | {h['color_icon']} {h['icon']}`\n"
    
    summary_text = (
        f"📋 *LAST 10 ROUNDS SUMMARY*\n\n"
        f"Issue | Pred | Result\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{table_rows}"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ WIN: {total_win} | ❌ LOSE: {total_lose}\n"
        f"📈 Rate: {win_rate:.1f}%\n"
        f"🔥 Max Streak: {max_win_streak}"
    )
    bot.send_message(MY_CHAT_ID, summary_text, parse_mode="Markdown")
    history_list = []

# ================= MAIN MONITOR =================
def start_monitoring():
    global LAST_PREDICTED_ISSUE, LAST_PREDICTION_SIZE, LAST_PREDICTION_COLOR
    global total_win, total_lose, current_win_streak, max_win_streak, current_lose_streak, max_lose_streak
    
    print("Bot started monitoring...")
    
    while True:
        try:
            data = fetch_data()
            if not data:
                time.sleep(15)
                continue
                
            latest_issue = str(data[0]["issueNumber"])
            
            # ၁။ ရလဒ် စစ်ဆေးခြင်း
            if LAST_PREDICTED_ISSUE == latest_issue:
                actual_num = data[0]["number"]
                actual_size = get_size(actual_num)
                actual_color = get_color(actual_num)
                size_win = (actual_size == LAST_PREDICTION_SIZE)
                
                icon = "✅" if size_win else "❌"
                color_icon = "🟢" if actual_color == "GREEN" else "🔴" if actual_color == "RED" else "🟣"
                
                if size_win:
                    total_win += 1
                    current_win_streak += 1
                    current_lose_streak = 0
                    max_win_streak = max(max_win_streak, current_win_streak)
                else:
                    total_lose += 1
                    current_lose_streak += 1
                    current_win_streak = 0
                    max_lose_streak = max(max_lose_streak, current_lose_streak)
                
                history_list.append({
                    "issue": latest_issue, "pred_size": LAST_PREDICTION_SIZE,
                    "actual_size": actual_size, "color_icon": color_icon, "icon": icon
                })
                
                bot.send_message(MY_CHAT_ID, 
                    f"📊 *RESULT: {latest_issue}*\n"
                    f"🎲 Num: `{actual_num}` | Size: *{actual_size}*\n"
                    f"🌈 Color: {color_icon} | Prediction: {icon}", 
                    parse_mode="Markdown")
                
                if len(history_list) >= 10:
                    send_summary()
                LAST_PREDICTED_ISSUE = None

            # ၂။ ခန့်မှန်းချက်အသစ်ထုတ်ခြင်း
            next_issue = str(int(latest_issue) + 1)
            if LAST_PREDICTED_ISSUE is None:
                pred_size, pred_color, size_conf, color_conf = pro_predict(data)
                color_emoji = "🔴" if pred_color == "RED" else "🟢" if pred_color == "GREEN" else "🟣"
                
                pred_text = (
                    f"💎 *6Lottery Wingo 30sULTRA SIGNAL By Mr.Team*\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📍 Period: `{next_issue}`\n"
                    f"📏 Size: *{pred_size}* ({size_conf}%)\n"
                    f"🌈 Color: {color_emoji} {pred_color} ({color_conf}%)\n"
                    f"━━━━━━━━━━━━━━━"
                )
                bot.send_message(MY_CHAT_ID, pred_text, parse_mode="Markdown")
                LAST_PREDICTED_ISSUE = next_issue
                LAST_PREDICTION_SIZE = pred_size
                LAST_PREDICTION_COLOR = pred_color
                
        except Exception as e:
            print(f"Loop Error: {e}")
            
        time.sleep(15) # Server Load သက်သာအောင် ၁၅ စက္ကန့်ထားပါ

if __name__ == "__main__":
    # Flask ကို Thread နဲ့ Run မယ်
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()
    
    # Bot Monitoring စမယ်
    start_monitoring()
