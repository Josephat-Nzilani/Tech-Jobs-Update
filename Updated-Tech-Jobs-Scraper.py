import csv
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Your Telegram Bot Token (get from @BotFather)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN_HERE")

def scrape_jobs():
    """Scrapes job listings from the website"""
    print("Fetching available jobs today.....")
    
    # Set up Selenium
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Load page
        url = "https://www.swejobpostings.com/job-listings.html"
        driver.get(url)
        time.sleep(10)
        
        # Get page source
        html = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract job listings
        jobs = soup.find_all("div", class_="job-card")
        job_list = []
        
        for job in jobs:
            title = job.find("h3", class_="job-card-title").text.strip()
            description = " | ".join([p.text.strip() for p in job.find_all("p")])
            link = job.find("a", class_="btn btn-primary")
            job_url = link["href"] if link else "N/A"
            job_list.append([title, description, job_url])
        
        return job_list
    
    finally:
        driver.quit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued"""
    await update.message.reply_text(
        "👋 Welcome to the Job Scraper Bot!\n\n"
        "Available commands:\n"
        "/jobs - Get latest job listings in table format\n"
        "/help - Show this help message"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued"""
    await update.message.reply_text(
        "📋 *Job Scraper Bot Help*\n\n"
        "/start - Start the bot\n"
        "/jobs - Get latest job listings in table format\n"
        "/help - Show this help message\n\n"
        "The bot scrapes jobs from swejobpostings.com and displays them in a formatted table with job title, description, and URL.",
        parse_mode='Markdown'
    )

async def get_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scrape and send job listings as formatted table"""
    await update.message.reply_text("🔍 Fetching available jobs... Please wait...")
    
    try:
        job_list = scrape_jobs()
        
        if not job_list:
            await update.message.reply_text("❌ No jobs found at the moment.")
            return
        
        # Format jobs as a table
        message = f"✅ *Found {len(job_list)} jobs today:*\n\n"
        message += "```\n"
        message += f"{'#':<4}{'JOB TITLE':<40}\n"
        message += "="*80 + "\n"
        
        for idx, job in enumerate(job_list, 1):
            title, description, url = job
            # Truncate title if too long
            title_short = title[:37] + "..." if len(title) > 40 else title
            message += f"{idx:<4}{title_short:<40}\n"
            message += f"    📝 {description[:70]}{'...' if len(description) > 70 else ''}\n"
            message += f"    🔗 {url}\n"
            message += "-"*80 + "\n"
            
            # Send in chunks if message gets too long (Telegram limit ~4096 chars)
            if len(message) > 3500:
                message += "```"
                await update.message.reply_text(message, parse_mode='Markdown')
                message = "```\n"
        
        message += "```"
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error occurred: {str(e)}")

async def get_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Scrape jobs and send as CSV file"""
    await update.message.reply_text("🔍 Fetching jobs and preparing CSV... Please wait...")
    
    try:
        job_list = scrape_jobs()
        
        if not job_list:
            await update.message.reply_text("❌ No jobs found at the moment.")
            return
        
        filename = save_to_csv(job_list)
        
        # Send the CSV file
        with open(filename, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename=filename,
                caption=f"✅ Found {len(job_list)} jobs!\n📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        
        # Clean up the file after sending
        os.remove(filename)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error occurred: {str(e)}")

def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("jobs", get_jobs))
    
    # Start the Bot
    print("Bot is running...")
    
    # Check if running in Jupyter/IPython/Spyder environment
    try:
        import nest_asyncio
        nest_asyncio.apply()
        print("Running in Spyder/Jupyter environment - nest_asyncio applied")
    except ImportError:
        print("nest_asyncio not found. If running in Spyder, install it: pip install nest_asyncio")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
