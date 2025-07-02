"""
Step 1: Determine if the invoice is saved in the database or not:
Store all invoice items in a list, then compare items with invoice number, name, national id, and phone number. if they
match, then the invoice has been already issued, otherwise there is no invoice file.
Step 2: Uploading the files in the email:
If there is already a file saved, load that file and send it to the customer through email. If there is no invoice file,
create a temporary invoice file, send it via email, then delete the temp file.
Step 3: Update the user's info. If the customer does not have an email address, add it to their query.
Step 4: Saving suggestion:
Suggest the user to save the invoice, if the invoice has not been already saved. if no, skip it. If the user does not
save the invoice, it will not appear in the database.
"""

import sqlite3
import os
import smtplib
from PySide6.QtWidgets import QDialog, QMessageBox
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Get the directory where documents_widget.py is located
module_dir = os.path.dirname(os.path.abspath(__file__))

# Go up one level to the parent directory (MotarjemYar1.06)
parent_dir = os.path.dirname(module_dir)

invoices_database = os.path.join(parent_dir, 'databases', 'invoices.db')
customers_database = os.path.join(parent_dir, 'databases', 'customers.db')


class SaveInvoice(QDialog):
    def __init__(self, parent_send_invoice):
        super().__init__()

        from qt_designer_ui.save_invoice_dialog import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.parent_send_invoice = parent_send_invoice

        self.ui.cancel_button.clicked.connect(self.reject)
        self.ui.ok_button.clicked.connect(self.save_super_parent_invoice)

    def save_super_parent_invoice(self):
        try:
            # Call the parent's save method and ignore its return value.
            self.parent_send_invoice.save_parent_invoice()
        finally:
            # This will be executed regardless of the parent's method return value.
            self.accept()


class SendInvoice(QDialog):
    def __init__(self, parent_invoice_preview):
        super().__init__()

        from qt_designer_ui.send_invoice import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.parent_invoice_preview = parent_invoice_preview

        self.SMTP_SERVER = "smtp.gmail.com"
        self.SMTP_PORT = 587
        self.SENDER_EMAIL = "translator663@gmail.com"
        self.SENDER_PASSWORD = "olpg azit xbpk ozfr"

        self.invoice_no = self.parent_invoice_preview.invoice_no
        self.customer_name = self.parent_invoice_preview.customer_name
        self.national_id = self.parent_invoice_preview.national_id
        self.phone_no = self.parent_invoice_preview.phone_no
        self.delivery_date = self.parent_invoice_preview.delivery_date
        self.issue_date = self.parent_invoice_preview.issue_date
        self.tro_name = "دارالترجمه دکتر زارعی"
        self.total_pages = self.parent_invoice_preview.calculate_total_pages()
        self.invoice_data = self.parent_invoice_preview.extract_data_from_invoice_table()
        self.file_path = self.parent_invoice_preview.is_invoice_saved(self.invoice_data)

        self.set_placeholders()
        
        self.ui.send_mail_button.clicked.connect(lambda: self._send_email(subject, body))
        self.ui.cancel_button.clicked.connect(self.reject)

        subject, body = self.set_email_placeholders()
        self.set_sms_placeholders()

    def set_placeholders(self):
        """Sets placeholder texts for Email subject and body"""
        if self.file_path is None:
            subject = "فاکتور شما صادر شد"
            invoice_number = ""
            self.ui.email_title_le.setPlaceholderText(subject)
        else:
            subject = f"فاکتور شماره {self.invoice_no}"
            invoice_number = self.invoice_no
            self.ui.email_title_le.setPlaceholderText(subject)

        # HTML Email Body
        body = f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #007bff;">{self.customer_name} عزیز,</h2>
                    <p>فاکتور شما نزد دارالترجمه دکتر زارعی صادر و در تاریخ {self.delivery_date} تحویل داده خواهد شد</p>
                    <p>لطفا در روز و ساعت تحویل فاکتور در دارالترجمه حضور داشته باشید</p>
                    <p> {"[توضیحات: ]"}</p>            
                    <p>با آروزی موفقیت</p>
                    <p><strong>دارالترجمه دکتر زارعی</strong></p>
                </body>
                </html>
                """
        self.ui.email_text_te.setPlaceholderText(body)

        link = ""
        self.ui.fil_link_le.setPlaceholderText(link)

        text = f"""
                        <html>
                        <body style="font-family: Arial, sans-serif;">
                            <h2 style="color: #007bff;">{self.customer_name} عزیز,</h2>
                            <p>فاکتور شما با شماره {invoice_number}نزد دارالترجمه دکتر زارعی صادر و در تاریخ {self.delivery_date} تحویل داده خواهد شد</p>
                            <p>لطفا در روز و ساعت تحویل فاکتور در دارالترجمه حضور داشته باشید</p>
                            <p>فاکتور خود را از طرق لینک زیر دانلود کنید:</p>            
                            <p>{link}</p>
                            <p><strong>دارالترجمه دکتر زارعی</strong></p>
                        </body>
                        </html>
                        """
        self.ui.sms_textbox.setPlaceholderText(text)

    def _create_email_message(self, customer_email):
        """Creates an email message with the required body content."""
        msg = MIMEMultipart()
        msg["From"] = self.SENDER_EMAIL
        msg["To"] = customer_email
        subject = self.ui.email_title_le.text().strip()
        msg["Subject"] = subject
        email_body = self.ui.email_text_te.toHtml()

        msg.attach(MIMEText(email_body, "html"))
        return msg

    def _attach_invoice_to_email(self, msg, invoice_number):
        """Attaches the correct invoice file to the email."""
        file_path = self.lookup_invoice_file(invoice_number)
        if file_path is None:
            QMessageBox.warning(self, "خطا", "فاکتور مورد نظر یافت نشد")
            return

        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)

            # Extract filename correctly
            filename = os.path.basename(file_path)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)

    def _attach_temporary_invoice_to_email(self, msg):
        """Attaches the correct invoice file to the email."""
        if self.total_pages == 1:
            file_path = "invoice.png"
            with self._create_temporary_invoice(file_path, "png"):
                try:
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)

                        # Extract filename correctly
                        filename = os.path.basename(file_path)
                        part.add_header("Content-Disposition", f"attachment; filename={filename}")
                        msg.attach(part)

                except AttributeError as e:
                    QMessageBox.warning(self, "خطا", f"{e}")

        if self.total_pages > 1:
            file_path = "invoice.pdf"
            with self._create_temporary_invoice(file_path, "pdf"):
                try:
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)

                        # Extract filename correctly
                        filename = os.path.basename(file_path)
                        part.add_header("Content-Disposition", f"attachment; filename={filename}")
                        msg.attach(part)

                except AttributeError as e:
                    QMessageBox.warning(self, "خطا", f"{e}")

    def _send_email(self, msg, customer_email):
        """Sends the email and returns True if successful, False otherwise."""
        try:
            server = smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT)
            server.starttls()
            server.login(self.SENDER_EMAIL, self.SENDER_PASSWORD)
            server.sendmail(self.SENDER_EMAIL, customer_email, msg.as_string())
            server.quit()

            QMessageBox.information(self, "موفقیت", f"✅ فاکتور به {customer_email} ارسال شد")
            return True
        except smtplib.SMTPAuthenticationError:
            QMessageBox.critical(self, "خطا", "❌ احراز هویت ایمیل ناموفق بود. رمز عبور یا تنظیمات SMTP را بررسی کنید.")
        except smtplib.SMTPException as e:
            QMessageBox.warning(self, "خطا", f"❌ خطای ارسال ایمیل:\n {e}")
        return False

    def _update_customer_database(self, customer_email):
        """Updates the customer database with the latest email address."""
        try:
            with sqlite3.connect(customers_database) as connection:
                cursor = connection.cursor()

                cursor.execute("""
                    INSERT INTO customers (national_id, name, phone, email)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(national_id) DO UPDATE SET email = excluded.email
                """, (self.national_id, self.customer_name, self.phone_no, customer_email))

                connection.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Error saving invoice: {e}")

    def _create_temporary_invoice(self, file_path, file_type):
        """Creates a temporary invoice file (PNG or PDF)."""
        if file_type == "png":
            self.parent_invoice_preview.save_invoice_as_png(file_path)
        elif file_type == "pdf":
            self.parent_invoice_preview.save_invoice_as_pdf(file_path)

        yield  # Context manager functionality
        if os.path.exists(file_path):
            os.remove(file_path)

    def lookup_invoice_file(self, invoice_number):
        """
        Look up the file_path in the issued_invoices table for a given invoice_number.
        """
        # Connect to the database
        with sqlite3.connect(invoices_database) as connection:
            try:
                cursor = connection.cursor()
                # Execute query to find the pdf_file_path for the given invoice_number
                cursor.execute(
                    "SELECT pdf_file_path FROM issued_invoices WHERE invoice_number = ?",
                    (invoice_number,)
                )
                row = cursor.fetchone()

                if row and row[0]:  # If a valid pdf_file_path exists, return it
                    return row[0]

            except sqlite3.Error as e:
                QMessageBox.critical(self, "خطای پایگاه داده", f"{e}")

    def save_parent_invoice(self):
        self.parent_invoice_preview.save_invoice()

    def show_save_invoice(self):
        """Asks the user to save the invoice if it's not already saved."""
        self.save_invoice = SaveInvoice(self)
        self.save_invoice.exec()
