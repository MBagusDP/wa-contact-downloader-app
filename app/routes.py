"""
Flask API for WA Contacts Downloader
"""

# Import necessary modules
from flask import jsonify, make_response, request, render_template, current_app, redirect
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
import qrcode
import os

# Create Flask application
app = create_app()


@app.route('/', methods=['POST','GET'])
def home():
    return render_template("mainPage.html")


@app.route('/tutorialPage')
def tutorialPage():
    return render_template("tutorialPage.html")


@app.route('/loadingPage')
def loadingPage():
    chat_filter = request.args.get('chatFilter')
    loading_text = request.args.get('loadingText')
    return render_template('loadingPage.html', chatFilter=chat_filter, loadingText=loading_text)


@app.route('/completedPage')
def completedPage():
    file_name = request.args.get('fileName')
    return render_template("completedPage.html", fileName=file_name)


@app.route('/developersPage', methods=['POST'])
def developersPage():
    develMsg = request.form.get('develMsg')
    return render_template("developersPage.html", develMsg=develMsg)


@app.route('/downloadFile')
def downloadFile():
    file_name = request.args.get('fileName')
    df = pd.read_excel(file_name)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=file_name.replace(
            '.xlsx', ''), index=False)
    output.seek(0)
    response = make_response(output)
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename='+file_name
    os.remove(file_name)
    return response


@app.route('/WAQRCodeDownloader')
def WAQRDownloader():
    chat_filter = request.args.get('chatFilter')
    loading_text = request.args.get('loadingText')
    # keyword_search = request.args.get('keywordSearch')
    try:
        URL = 'https://web.whatsapp.com'
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        driver = webdriver.Chrome(options=options)
        driver.get(URL)
        WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="_19vUU"]')))
        qr_data_code = None
        for i in range(0,10):
            time.sleep(1)
            if qr_data_code is None:
                qr_data_code = driver.find_element(By.XPATH, '//div[@class="_19vUU"]').get_attribute('data-ref')
            else:
                break
        qrcode.make(qr_data_code).save('image/wa_qrcode.png')
        current_app.driver = driver
        
        # return render_template("waQrCodeScanPage.html", chatFilter=chat_filter, loadingText=loading_text, keywordSearch=keyword_search)
        return render_template("waQrCodeScanPage.html", chatFilter=chat_filter, loadingText=loading_text)
    except:
        driver.close()
        if 'Message: no such window: target window already closed' in str(traceback.format_exc()):
            return render_template("browserClosedPage.html")
        else:
            return render_template("programExitErrorPage.html", error=traceback.format_exc())


@app.route('/WAQRScanDetector')
def WAQRScanDetector():
    chat_filter = request.args.get('chatFilter')
    loading_text = request.args.get('loadingText')
    # keyword_search = request.args.get('keywordSearch')
    driver = current_app.driver
    try:
        WebDriverWait(driver, 100).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="_3RpB9"]')))
        os.remove('image/wa_qrcode.png')
        current_app.driver = driver
        # return render_template('loadingPage.html', chatFilter=chat_filter, loadingText=loading_text, keywordSearch=keyword_search)
        return render_template('loadingPage.html', chatFilter=chat_filter, loadingText=loading_text)
    except:
        driver.close()
        if 'Message: no such window: target window already closed' in str(traceback.format_exc()):
            return render_template("browserClosedPage.html")
        else:
            return render_template("programExitErrorPage.html", error=traceback.format_exc())
    

@app.route('/WAContactsDownloader')
def WAContactsDownloader():
    chat_filter = request.args.get('chatFilter')
    driver = current_app.driver
    try:
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
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@aria-label="Search results."]')))
        chat_num = int(driver.find_element(By.XPATH, '//div[@aria-label="Search results."]').get_attribute('aria-rowcount'))
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
        driver.close()
        df = pd.DataFrame(contacts, columns=['contacts','date']).drop_duplicates()
        file_name = '{date} {chatFilter} WA.xlsx'.format(date=str(datetime.datetime.now().date()), chatFilter=chat_filter)
        df.to_excel(file_name, index=False)
        return redirect(f'/completedPage?fileName={file_name}')
    # chat_filter = request.args.get('chatFilter')
    # keyword_search = request.args.get('keywordSearch')
    # driver = current_app.driver
    # try:
    #     WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@role="textbox"]')))
    #     driver.find_element(By.XPATH, '//div[@role="textbox"]').send_keys(keyword_search)
    #     for i in range(1,0):
    #         time.sleep(1)
    #         WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@role="textbox"]')))
    #         if driver.find_element(By.XPATH, '//div[@role="textbox"]').text == keyword_search:
    #             print("text: "+driver.find_element(By.XPATH, '//div[@role="textbox"]').text)
    #             break
    #     if chat_filter != 'Chats' or keyword_search != '':
    #         for i in range(0,10):
    #             try:
    #                 WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.XPATH, f'//div[contains(text(), "{chat_filter}")]')))
    #                 driver.find_element(By.XPATH, f'//div[contains(text(), "{chat_filter}")]').click()
    #             except:
    #                 WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.XPATH, '//button[@aria-label="Chat filters menu"]')))
    #                 driver.find_element(By.XPATH, '//button[@aria-label="Chat filters menu"]').click()
    #             WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.XPATH, '//button[@aria-label="Chat filters menu"]')))
    #             if driver.find_element(By.XPATH, '//button[@aria-label="Chat filters menu"]').get_attribute('aria-pressed') == 'true':
    #                 break
    #         if chat_filter in ['Contacts','Non-contacts','Groups'] or keyword_search != '':
    #             WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@aria-label="Search results."]')))
    #             chat_num = int(driver.find_element(By.XPATH, '//div[@aria-label="Search results."]').get_attribute('aria-rowcount'))
    #         else:
    #             WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@aria-label="Chat list"]')))
    #             chat_num = int(driver.find_element(By.XPATH, '//div[@aria-label="Chat list"]').get_attribute('aria-rowcount'))
    #     else:
    #         WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@aria-label="Chat list"]')))
    #         chat_num = int(driver.find_element(By.XPATH, '//div[@aria-label="Chat list"]').get_attribute('aria-rowcount'))
    #     contacts = []
    #     for i in range(0,int((chat_num)/19)+1):
    #         if i*19*72 <= chat_num*72:
    #             px = i*19*72
    #         else:
    #             px = chat_num*72
    #         WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@id="pane-side"]')))
    #         driver.execute_script(f"document.querySelector('div[id=\"pane-side\"]').scrollTo(0,{px});")
    #         WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@role="listitem"]')))
    #         for elem in driver.find_elements(By.XPATH, '//div[@role="listitem"]'):
    #             WebDriverWait(elem, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@role="listitem"]')))
    #             contacts.append(elem.text.split('\n')[0:2])
    #     driver.close()
    #     df = pd.DataFrame(contacts, columns=['contacts','date']).drop_duplicates()
    #     file_name = '{date} {chatFilter} WA.xlsx'.format(date=str(datetime.datetime.now().date()), chatFilter=chat_filter)
    #     df.to_excel(file_name, index=False)
    #     return redirect(f'/completedPage?fileName={file_name}')
    except:
        driver.close()
        if 'Message: no such window: target window already closed' in str(traceback.format_exc()):
            return render_template("browserClosedPage.html")
        else:
            return render_template("programExitErrorPage.html", error=traceback.format_exc())


@app.errorhandler(404)
def not_found(e):
    return jsonify(error=str(e)), 404