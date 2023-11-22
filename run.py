from app.routes import app
import webview

window = webview.create_window('MBagusDP Whatsapp Unsaved Contacts Downloader',app)

if __name__ == '__main__':
    # app.run(debug=True)
    webview.start()