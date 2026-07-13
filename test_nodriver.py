import asyncio
import nodriver as uc
import sys

async def main():
    try:
        print("Starting nodriver...")
        browser = await uc.start()
        print("Browser started. Navigating to Blackwoods...")
        page = await browser.get('https://www.blackwoods.com.au/search?q=drill')
        
        # Wait a bit for JS to render
        await asyncio.sleep(5)
        
        content = await page.get_content()
        print(f"Blackwoods Content length: {len(content)}")
        with open("bw_nodriver.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Navigating to Sydney Tools...")
        page2 = await browser.get('https://sydneytools.com.au/search?q=drill')
        await asyncio.sleep(5)
        
        content2 = await page2.get_content()
        print(f"Sydney Tools Content length: {len(content2)}")
        with open("st_nodriver.html", "w", encoding="utf-8") as f:
            f.write(content2)
            
        browser.stop()
        print("Done.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
