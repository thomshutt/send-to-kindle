import smtplib, os
import sys
from bottle import get, post, run, request 
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

if len(sys.argv) != 4:
    print "Usage: "
    print "    python SendToKindle.py <email_from> <email_to> <port>"
    sys.exit() 

email_from = sys.argv[1]
email_to = sys.argv[2]
port = sys.argv[3]

def send_mail(send_from, send_to, subject, text, files=[], server="localhost"):
    assert isinstance(send_to, list)
    assert isinstance(files, list)

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        msg.attach(part)

    smtp = smtplib.SMTP('localhost')
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()

@get('/kindle')
def login():
    return '''
        <form action="/kindle" method="post">
            Title: <input name="title" type="text" /><br />
            Content: <textarea name="content" rows="6" cols="50"></textarea><br />
            <input value="Send To Kindle" type="submit" />
        </form>
        <form action="/kindlefile" method="post" enctype="multipart/form-data">
            File: <input name="upload" type="file" /><br />
            <input value="Send To Kindle" type="submit" />
        </form>
    '''

@post('/kindlefile')
def deal_with_file():
    upload = request.files.get('upload')
    name, ext = os.path.splitext(upload.filename)

    if ext not in ('.txt','.pdf','.mobi', '.epub'):
        return 'File extension not allowed.'

    # Get the data
    raw = upload.value;

    # Write to file
    filename = "tmp" + ext
    with open(filename, 'wb') as f:
        f.write(raw)

    os.system("ebook-convert tmp" + ext + " tmp.mobi")

    send_mail(email_from, [email_to], "", "", ["tmp.mobi"])

    return '<p>Sent.</p>'

@post('/kindle')
def do_login():
    title = request.forms.get('title')
    content = request.forms.get('content')

    text_file = open("tmp.txt", "w")
    text_file.write(content)
    text_file.close()

    os.system("ebook-convert tmp.txt tmp.mobi --title \"" + title + "\"")

    send_mail(email_from, [email_to], title, "", ["tmp.mobi"])
 
    return "<p>Sent.</p>"



run(host='localhost', port=int(port), reloader=True)
