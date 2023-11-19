"""
Flask API for WA Contacts Downloader
"""

# Import necessary modules
from flask import jsonify, make_response, request, send_file, after_this_request, render_template
from app import create_app
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import datetime
import io
import pandas as pd
import traceback

# Create Flask application
app = create_app()


@app.route('/', methods=['POST','GET'])
def home():
    return render_template("mainPage.html")


@app.route('/tutorialPage')
def tutorialPage():
    return render_template("tutorialPage.html")


@app.route('/developersPage', methods=['POST'])
def developersPage():
    develMsg = request.form.get('develMsg')
    return render_template("developersPage.html", develMsg=develMsg)


@app.route('/WAContactsDownloader')
def wa_contacts_downloader():
    try:
        chat_filter = request.args.get('chatFilter')
        URL = 'https://web.whatsapp.com'
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(options=options)
        driver.get(URL)
        WebDriverWait(driver, 100).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="_3RpB9"]')))
        if chat_filter != '':
            for i in range(0,10):
                try:
                    WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.XPATH, f'//div[contains(text(), "{chat_filter}")]')))
                    driver.find_element(By.XPATH, f'//div[contains(text(), "{chat_filter}")]').click()
                except:
                    WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.XPATH, '//button[@aria-label="Chat filters menu"]')))
                    driver.find_element(By.XPATH, '//button[@aria-label="Chat filters menu"]').click()
                WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.XPATH, '//button[@aria-label="Chat filters menu"]')))
                if driver.find_element(By.XPATH, '//button[@aria-label="Chat filters menu"]').get_attribute('aria-pressed') == 'true':
                    break
            if chat_filter in ['Contacts','Non-contacts','Groups']:
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@aria-label="Search results."]')))
                chat_num = int(driver.find_element(By.XPATH, '//div[@aria-label="Search results."]').get_attribute('aria-rowcount'))
            else:
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@aria-label="Chat list"]')))
                chat_num = int(driver.find_element(By.XPATH, '//div[@aria-label="Chat list"]').get_attribute('aria-rowcount'))
        else:
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@aria-label="Chat list"]')))
            chat_num = int(driver.find_element(By.XPATH, '//div[@aria-label="Chat list"]').get_attribute('aria-rowcount'))
        contacts = []
        for i in range(0,int((chat_num)/19)+1):
            if i*19*72 <= chat_num*72:
                px = i*19*72
            else:
                px = chat_num*72
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@id="pane-side"]')))
            driver.execute_script(f"document.querySelector('div[id=\"pane-side\"]').scrollTo(0,{px});")
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@role="listitem"]')))
            for elem in driver.find_elements(By.XPATH, '//div[@role="listitem"]'):
                WebDriverWait(elem, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@role="listitem"]')))
                contacts.append(elem.text.split('\n')[0:2])
        time.sleep(3)
        driver.close()

        # Create a response with Excel content
        df = pd.DataFrame(contacts, columns=['contacts','date']).drop_duplicates()
        path = 'app\\'
        file_name = '{date} {chatFilter} WA.xlsx'.format(date=str(datetime.datetime.now().date()), chatFilter=chat_filter)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=file_name.replace(
                '.xlsx', ''), index=False)
        output.seek(0)
        response = make_response(output)
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = 'attachment; filename='+file_name

        return response
    except:
        # error = e
        print(">>>>>>>>>>>>>>>>>>>>>>> THE ERROR IS:")
        print(traceback.format_exc())
        if 'Message: no such window: target window already closed' in str(traceback.format_exc()):
            return render_template("browserClosedPage.html")
        else:
            return render_template("programExitErrorPage.html", error=traceback.format_exc())


@app.errorhandler(404)
def not_found(e):
    """
    Error handler for 404 Not Found

    Args:
        e (Exception): Exception object

    Returns:
        dict: JSON response containing the error message
    """
    return jsonify(error=str(e)), 404