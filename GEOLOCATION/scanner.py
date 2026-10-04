import os
import re
import ipaddress
import sys

import IP2Location
import IP2Proxy

from email import policy
from email.parser import BytesParser


# LOAD NLP MODEL
NLP_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "NLP model")
)

sys.path.insert(0, NLP_DIR)

from email_nlp import analyze_email

# FOLDERS

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

incoming = os.path.join(
    BASE_DIR,
    "Incoming Emails"
)

reports = os.path.join(
    BASE_DIR,
    "Reports"
)


# CREATE REQUIRED FOLDERS

os.makedirs(
    incoming,
    exist_ok=True
)

os.makedirs(
    reports,
    exist_ok=True
)


# DATABASES

location_db = IP2Location.IP2Location(
    os.path.join(
        BASE_DIR,
        "IP2Location",
        "IP2LOCATION-LITE-DB11.BIN"
    )
)


proxy_db = IP2Proxy.IP2Proxy()

proxy_db.open(
    os.path.join(
        BASE_DIR,
        "IP2PROXY",
        "IP2PROXY-LITE-PX12.BIN"
    )
)


# KNOWN MAIL PROVIDERS

mail_providers = {

    "Google": [
        "google.com",
        "googlemail.com",
        "gmail.com"
    ],

    "Microsoft": [
        "outlook.com",
        "microsoft.com",
        "office365.com",
        "protection.outlook.com"
    ],

    "Yahoo": [
        "yahoo.com",
        "yahoo.co.uk",
        "yahoo.co.in"
    ],

    "Amazon": [
        "amazonaws.com",
        "amazonses.com"
    ],

    "SendGrid": [
        "sendgrid.net"
    ],

    "Mailgun": [
        "mailgun.org"
    ]
}


# IDENTIFY MAIL PROVIDER

def identify_mail_provider(header):

    header = header.lower()

    for provider, domains in mail_providers.items():

        for domain in domains:

            if domain in header:

                return provider

    return None


# EXTRACT PUBLIC IP ADDRESSES

def extract_ips(received_headers):

    ip_records = []

    for header in received_headers:

        found_ips = re.findall(
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            header
        )

        for ip in found_ips:

            try:

                address = ipaddress.ip_address(ip)

                if not address.is_global:

                    continue


                already_found = False

                for record in ip_records:

                    if record["ip"] == ip:

                        already_found = True

                        break


                if already_found:

                    continue


                provider = identify_mail_provider(
                    header
                )


                if provider:

                    role = "MAIL SERVER / RELAY"

                else:

                    role = "UNKNOWN / POSSIBLE ORIGIN"


                ip_records.append({

                    "ip": ip,

                    "header": header,

                    "provider": provider,

                    "role": role

                })


            except ValueError:

                pass


    return ip_records


# ANALYZE SPF DKIM DMARC

def analyze_authentication(email):

    auth_header = email.get(
        "Authentication-Results",
        ""
    )

    auth_header = str(
        auth_header
    ).lower()


    result = {

        "spf": "Not Available",

        "dkim": "Not Available",

        "dmarc": "Not Available"

    }


    # SPF

    spf_match = re.search(
        r"\bspf=(pass|fail|softfail|neutral|none|"
        r"temperror|permerror)\b",
        auth_header
    )


    if spf_match:

        result["spf"] = (
            spf_match.group(1).upper()
        )


    # DKIM

    dkim_match = re.search(
        r"\bdkim=(pass|fail|neutral|none|"
        r"temperror|permerror)\b",
        auth_header
    )


    if dkim_match:

        result["dkim"] = (
            dkim_match.group(1).upper()
        )


    # DMARC

    dmarc_match = re.search(
        r"\bdmarc=(pass|fail|bestguesspass|none|"
        r"temperror|permerror)\b",
        auth_header
    )


    if dmarc_match:

        result["dmarc"] = (
            dmarc_match.group(1).upper()
        )


    return result


# CALCULATE AUTHENTICATION SCORE

def calculate_authentication_score(
    authentication
):

    score = 0


    if authentication["spf"] == "FAIL":

        score += 20

    elif authentication["spf"] in [

        "SOFTFAIL",
        "PERMERROR",
        "TEMPERROR"

    ]:

        score += 10


    if authentication["dkim"] == "FAIL":

        score += 20

    elif authentication["dkim"] in [

        "PERMERROR",
        "TEMPERROR"

    ]:

        score += 10


    if authentication["dmarc"] == "FAIL":

        score += 30

    elif authentication["dmarc"] in [

        "PERMERROR",
        "TEMPERROR"

    ]:

        score += 15


    return score


# GET AUTHENTICATION RISK

def get_authentication_risk(score):

    if score == 0:

        return "LOW"

    elif score <= 20:

        return "MEDIUM"

    elif score <= 40:

        return "HIGH"

    else:

        return "CRITICAL"


# GET IP2PROXY INFORMATION

def get_proxy_information(ip):

    information = {

        "proxy_type": "Not Available",

        "isp": "Not Available",

        "domain": "Not Available",

        "usage_type": "Not Available",

        "asn": "Not Available",

        "proxy_status": "Not Available"

    }


    try:

        information["proxy_type"] = str(
            proxy_db.get_proxy_type(ip)
        )


        information["isp"] = str(
            proxy_db.get_isp(ip)
        )


        information["domain"] = str(
            proxy_db.get_domain(ip)
        )


        information["usage_type"] = str(
            proxy_db.get_usage_type(ip)
        )


        information["asn"] = str(
            proxy_db.get_asn(ip)
        )


        proxy_status = proxy_db.is_proxy(ip)


        if proxy_status == 0:

            information["proxy_status"] = (
                "No Proxy Detected"
            )

        else:

            information["proxy_status"] = (
                "Proxy / Anonymizer Detected"
            )


    except Exception:

        pass


    return information


# GET GEOLOCATION

def get_location_information(ip):

    information = {

        "country": "Not Available",

        "region": "Not Available",

        "city": "Not Available",

        "latitude": "Not Available",

        "longitude": "Not Available",

        "isp": "Not Available",

        "map_link": "Not Available"

    }


    try:

        location = location_db.get_all(ip)


        latitude = location.latitude

        longitude = location.longitude


        information["country"] = str(
            location.country_long
        )


        information["region"] = str(
            location.region
        )


        information["city"] = str(
            location.city
        )


        information["latitude"] = str(
            latitude
        )


        information["longitude"] = str(
            longitude
        )


        information["isp"] = str(
            location.isp
        )


        information["map_link"] = (

            f"https://www.google.com/maps?q="
            f"{latitude},{longitude}"

        )


    except Exception:

        pass


    return information


# EXTRACT EMAIL BODY

def extract_email_body(email):

    if email.is_multipart():

        for part in email.walk():

            content_type = part.get_content_type()

            content_disposition = str(
                part.get(
                    "Content-Disposition",
                    ""
                )
            )


            if (
                content_type == "text/plain"
                and
                "attachment" not in content_disposition
            ):

                try:

                    return part.get_content()

                except Exception:

                    pass


        for part in email.walk():

            content_type = part.get_content_type()

            content_disposition = str(
                part.get(
                    "Content-Disposition",
                    ""
                )
            )


            if (
                content_type == "text/html"
                and
                "attachment" not in content_disposition
            ):

                try:

                    return part.get_content()

                except Exception:

                    pass


        return ""


    try:

        return email.get_content()

    except Exception:

        return ""


# WRITE IP INFORMATION

def write_ip_analysis(
    report,
    ip_records
):

    report.write(
        "\nSOURCE ANALYSIS\n"
    )

    report.write(
        "------------------------------------------------------------\n"
    )


    if not ip_records:

        report.write(
            "Public IP       : Not Available\n"
        )

        report.write(
            "Location        : Not Available\n"
        )

        return


    for number, record in enumerate(
        ip_records,
        start=1
    ):

        ip = record["ip"]

        provider = record["provider"]

        role = record["role"]


        location = get_location_information(
            ip
        )


        proxy = get_proxy_information(
            ip
        )


        report.write(
            "\nIP Address      : "
            + ip
            + "\n"
        )


        report.write(
            "Role            : "
            + role
            + "\n"
        )


        if provider:

            report.write(
                "Mail Provider   : "
                + provider
                + "\n"
            )


        report.write(
            "Country         : "
            + location["country"]
            + "\n"
        )


        report.write(
            "Region          : "
            + location["region"]
            + "\n"
        )


        report.write(
            "City            : "
            + location["city"]
            + "\n"
        )


        report.write(
            "ISP             : "
            + location["isp"]
            + "\n"
        )


        report.write(
            "Proxy           : "
            + proxy["proxy_status"]
            + "\n"
        )


        report.write(
            "Proxy Type      : "
            + proxy["proxy_type"]
            + "\n"
        )


        report.write(
            "ASN             : "
            + proxy["asn"]
            + "\n"
        )


        report.write(
            "Map             : "
            + location["map_link"]
            + "\n"
        )


# WRITE SENDER LOCATION

def write_sender_location(
    report,
    ip_records
):

    report.write(
        "\nSENDER LOCATION\n"
    )

    report.write(
        "------------------------------------------------------------\n"
    )


    possible_origin = False


    for record in ip_records:

        if record["role"] == (
            "UNKNOWN / POSSIBLE ORIGIN"
        ):

            possible_origin = True

            break


    if possible_origin:

        report.write(
            "Possible Origin : Public IP found\n"
        )

        report.write(
            "Note            : IP geolocation is an estimate.\n"
        )


    else:

        report.write(
            "Result          : Sender device IP not available\n"
        )

        report.write(
            "Reason          : Available IPs appear to be "
            "mail servers or relays.\n"
        )


# SCAN EMAIL

def scan_email(
    filepath,
    filename
):

    print()

    print(
        "========================================"
    )

    print(
        "Scanning:",
        filename
    )

    print(
        "========================================"
    )


    # READ EMAIL

    try:

        with open(
            filepath,
            "rb"
        ) as file:

            email = BytesParser(
                policy=policy.default
            ).parse(file)


    except Exception as error:

        print(
            "Error reading email:",
            error
        )

        return False


    # EMAIL INFORMATION

    sender = email.get(
        "From",
        "Unknown"
    )


    receiver = email.get(
        "To",
        "Unknown"
    )


    subject = email.get(
        "Subject",
        "Unknown"
    )


    date = email.get(
        "Date",
        "Unknown"
    )


    reply_to = email.get(
        "Reply-To",
        "Not Available"
    )


    return_path = email.get(
        "Return-Path",
        "Not Available"
    )


    # EXTRACT BODY

    body = extract_email_body(
        email
    )


    # NLP ANALYSIS

    try:

        nlp_result = analyze_email(
            str(sender),
            str(subject),
            str(body)
        )


    except Exception as error:

        print(
            "NLP analysis error:",
            error
        )


        nlp_result = {

            "threat": "Not Available",

            "confidence": 0,

            "risk": "Not Available"

        }


    # AUTHENTICATION

    authentication = analyze_authentication(
        email
    )


    auth_score = calculate_authentication_score(
        authentication
    )


    auth_risk = get_authentication_risk(
        auth_score
    )


    # RECEIVED HEADERS

    received_headers = email.get_all(
        "Received",
        []
    )


    # EXTRACT IPs

    ip_records = extract_ips(
        received_headers
    )


    # REPORT NAME

    report_name = (

        os.path.splitext(filename)[0]
        + "_Report.txt"

    )


    # REPORT PATH

    report_path = os.path.join(
        reports,
        report_name
    )


    # CREATE REPORT

    try:

        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as report:


            report.write(
                "============================================================\n"
            )


            report.write(
                "              EMAIL THREAT DETECTION REPORT\n"
            )


            report.write(
                "============================================================\n"
            )


            # THREAT SUMMARY

            report.write(
                "\nTHREAT SUMMARY\n"
            )


            report.write(
                "------------------------------------------------------------\n"
            )


            report.write(
                "Threat          : "
                + str(nlp_result["threat"])
                + "\n"
            )


            report.write(
                "Risk Level      : "
                + str(nlp_result["risk"])
                + "\n"
            )


            report.write(
                "Confidence      : "
                + str(nlp_result["confidence"])
                + "%\n"
            )


            # EMAIL DETAILS

            report.write(
                "\nEMAIL DETAILS\n"
            )


            report.write(
                "------------------------------------------------------------\n"
            )


            report.write(
                "File            : "
                + filename
                + "\n"
            )


            report.write(
                "From            : "
                + str(sender)
                + "\n"
            )


            report.write(
                "To              : "
                + str(receiver)
                + "\n"
            )


            report.write(
                "Subject         : "
                + str(subject)
                + "\n"
            )


            report.write(
                "Date            : "
                + str(date)
                + "\n"
            )


            report.write(
                "Reply-To        : "
                + str(reply_to)
                + "\n"
            )


            report.write(
                "Return-Path     : "
                + str(return_path)
                + "\n"
            )


            # AUTHENTICATION

            report.write(
                "\nEMAIL AUTHENTICATION\n"
            )


            report.write(
                "------------------------------------------------------------\n"
            )


            report.write(
                "SPF             : "
                + authentication["spf"]
                + "\n"
            )


            report.write(
                "DKIM            : "
                + authentication["dkim"]
                + "\n"
            )


            report.write(
                "DMARC           : "
                + authentication["dmarc"]
                + "\n"
            )


            report.write(
                "Authentication  : "
                + auth_risk
                + "\n"
            )


            # SOURCE ANALYSIS

            write_ip_analysis(
                report,
                ip_records
            )


            # SENDER LOCATION

            write_sender_location(
                report,
                ip_records
            )


            # END REPORT

            report.write(
                "\n============================================================\n"
            )


            report.write(
                "                    END OF REPORT\n"
            )


            report.write(
                "============================================================\n"
            )


    except Exception as error:

        print(
            "Error creating report:",
            error
        )

        return False


    # DELETE ORIGINAL EMAIL

    try:

        if os.path.exists(filepath):

            os.remove(filepath)

            print(
                "Email permanently deleted:",
                filename
            )


    except Exception as error:

        print(
            "Could not delete email:",
            error
        )

        return False


    # CONSOLE OUTPUT

    print(
        "NLP Threat:",
        nlp_result["threat"]
    )


    print(
        "NLP Confidence:",
        str(
            nlp_result["confidence"]
        ) + "%"
    )


    print(
        "NLP Risk:",
        nlp_result["risk"]
    )


    print(
        "SPF:",
        authentication["spf"]
    )


    print(
        "DKIM:",
        authentication["dkim"]
    )


    print(
        "DMARC:",
        authentication["dmarc"]
    )


    print(
        "Report created:",
        report_path
    )


    return True


# MAIN

def main():

    found_email = False


    for filename in os.listdir(
        incoming
    ):


        if not filename.lower().endswith(
            ".eml"
        ):

            continue


        found_email = True


        filepath = os.path.join(
            incoming,
            filename
        )


        scan_email(
            filepath,
            filename
        )


    if not found_email:

        print(
            "No .eml files found."
        )


    print()

    print(
        "========================================"
    )

    print(
        "          SCANNING COMPLETED"
    )

    print(
        "========================================"
    )


# START

if __name__ == "__main__":

    main()