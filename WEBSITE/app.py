from flask import Flask, render_template, request, send_file
import os
import subprocess
import sys
import glob


# WEBSITE PATH

WEBSITE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# PROJECT ROOT

BASE_DIR = os.path.dirname(
    WEBSITE_DIR
)


# GEOLOCATION PATH

GEOLOCATION_DIR = os.path.join(
    BASE_DIR,
    "GEOLOCATION"
)


# EMAIL FOLDER

INCOMING_DIR = os.path.join(
    GEOLOCATION_DIR,
    "Incoming Emails"
)


# REPORT FOLDER

REPORTS_DIR = os.path.join(
    GEOLOCATION_DIR,
    "Reports"
)


# SCANNER

SCANNER = os.path.join(
    GEOLOCATION_DIR,
    "scanner.py"
)


# FLASK APP

app = Flask(
    __name__,
    template_folder=os.path.join(
        WEBSITE_DIR,
        "templates"
    ),
    static_folder=os.path.join(
        WEBSITE_DIR,
        "static"
    )
)


# CHECK PATHS

print()
print("==============================")
print("PROJECT PATHS")
print("==============================")

print(
    "PROJECT       :",
    BASE_DIR
)

print(
    "WEBSITE       :",
    WEBSITE_DIR
)

print(
    "GEOLOCATION   :",
    GEOLOCATION_DIR
)

print(
    "SCANNER       :",
    SCANNER
)

print(
    "SCANNER EXISTS:",
    os.path.exists(SCANNER)
)

print("==============================")
print()


# CHECK REQUIRED FOLDERS

if not os.path.exists(GEOLOCATION_DIR):

    raise FileNotFoundError(
        "GEOLOCATION folder not found:\n"
        + GEOLOCATION_DIR
    )


if not os.path.exists(INCOMING_DIR):

    raise FileNotFoundError(
        "Incoming Emails folder not found:\n"
        + INCOMING_DIR
    )


if not os.path.exists(REPORTS_DIR):

    raise FileNotFoundError(
        "Reports folder not found:\n"
        + REPORTS_DIR
    )


if not os.path.isfile(SCANNER):

    raise FileNotFoundError(
        "scanner.py not found:\n"
        + SCANNER
    )


# LAST REPORT

app.config["LAST_REPORT"] = None


# HOME PAGE

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# SCAN EMAIL

@app.route(
    "/scan",
    methods=["POST"]
)
def scan_email():

    # CHECK FILE

    if "email" not in request.files:

        return render_template(
            "report.html",
            error="No email file was uploaded."
        )


    file = request.files["email"]


    # CHECK FILE NAME

    if file.filename == "":

        return render_template(
            "report.html",
            error="No file was selected."
        )


    # CHECK FILE TYPE

    if not file.filename.lower().endswith(".eml"):

        return render_template(
            "report.html",
            error="Only .eml files are supported."
        )


    # CLEAN FILE NAME

    filename = os.path.basename(
        file.filename
    )


    # EMAIL PATH

    email_path = os.path.join(
        INCOMING_DIR,
        filename
    )


    # SAVE EMAIL

    try:

        file.save(
            email_path
        )

    except Exception as error:

        return render_template(
            "report.html",
            error=(
                "Could not save the email.\n\n"
                f"{error}"
            )
        )


    # PRINT UPLOAD INFO

    print()
    print("==============================")
    print("EMAIL UPLOADED")
    print("==============================")
    print(filename)
    print()


    # GET OLD REPORTS

    old_reports = set(
        glob.glob(
            os.path.join(
                REPORTS_DIR,
                "*.txt"
            )
        )
    )


    # RUN SCANNER

    try:

        result = subprocess.run(
            [
                sys.executable,
                SCANNER
            ],
            cwd=GEOLOCATION_DIR,
            capture_output=True,
            text=True
        )

    except Exception as error:

        return render_template(
            "report.html",
            error=(
                "Could not start scanner.py.\n\n"
                f"{error}"
            )
        )


    # PRINT SCANNER OUTPUT

    print("==============================")
    print("SCANNER OUTPUT")
    print("==============================")

    print(result.stdout)


    print("==============================")
    print("SCANNER ERRORS")
    print("==============================")

    print(result.stderr)


    # CHECK SCANNER STATUS

    if result.returncode != 0:

        error_message = result.stderr

        if not error_message.strip():

            error_message = result.stdout


        return render_template(
            "report.html",
            error=(
                "Scanner failed.\n\n"
                f"Exit Code: {result.returncode}\n\n"
                f"{error_message}"
            )
        )


    # GET REPORTS AFTER SCANNING

    all_reports = set(
        glob.glob(
            os.path.join(
                REPORTS_DIR,
                "*.txt"
            )
        )
    )


    # FIND NEW REPORT

    new_reports = list(
        all_reports - old_reports
    )


    # NEW REPORT FOUND

    if new_reports:

        report_path = max(
            new_reports,
            key=os.path.getmtime
        )


    else:

        # GET ALL REPORTS

        reports = glob.glob(
            os.path.join(
                REPORTS_DIR,
                "*.txt"
            )
        )


        # NO REPORT FOUND

        if not reports:

            return render_template(
                "report.html",
                error=(
                    "Scanner completed successfully, "
                    "but no report was generated."
                )
            )


        # GET MOST RECENT REPORT

        report_path = max(
            reports,
            key=os.path.getmtime
        )


    # READ REPORT

    try:

        with open(
            report_path,
            "r",
            encoding="utf-8"
        ) as report_file:

            report = report_file.read()

    except Exception as error:

        return render_template(
            "report.html",
            error=(
                "Could not read the generated report.\n\n"
                f"{error}"
            )
        )


    # SAVE LAST REPORT

    app.config[
        "LAST_REPORT"
    ] = report_path


    # PRINT REPORT INFO

    print()
    print("==============================")
    print("REPORT GENERATED")
    print("==============================")

    print(
        os.path.basename(
            report_path
        )
    )

    print()


    # SHOW REPORT

    return render_template(
        "report.html",
        report=report,
        report_name=os.path.basename(
            report_path
        )
    )


# DOWNLOAD REPORT

@app.route(
    "/download-report"
)
def download_report():

    # GET LAST REPORT

    report_path = app.config.get(
        "LAST_REPORT"
    )


    # NO REPORT

    if not report_path:

        return render_template(
            "report.html",
            error="No report is available."
        )


    # REPORT DOES NOT EXIST

    if not os.path.exists(
        report_path
    ):

        return render_template(
            "report.html",
            error="The report no longer exists."
        )


    # DOWNLOAD REPORT

    return send_file(
        report_path,
        as_attachment=True,
        download_name=os.path.basename(
            report_path
        )
    )


# START SERVER

if __name__ == "__main__":

    app.run(
        debug=True
    )