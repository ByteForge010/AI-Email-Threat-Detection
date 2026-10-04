const uploadBox =
    document.getElementById("uploadBox");

const emailInput =
    document.getElementById("emailInput");

const chooseButton =
    document.getElementById("chooseButton");

const selectedFile =
    document.getElementById("selectedFile");

const emailForm =
    document.getElementById("emailForm");


// CHOOSE FILE / ANALYZE EMAIL

chooseButton.addEventListener(
    "click",
    function (event) {

        event.stopPropagation();


        // NO FILE = CHOOSE FILE

        if (emailInput.files.length === 0) {

            emailInput.click();

        }


        // FILE EXISTS = ANALYZE

        else {

            chooseButton.disabled = true;

            chooseButton.innerHTML =
                "Analyzing Email...";

            emailForm.submit();

        }

    }
);


// CLICK UPLOAD BOX

uploadBox.addEventListener(
    "click",
    function () {

        if (
            emailInput.files.length === 0
        ) {

            emailInput.click();

        }

    }
);


// FILE SELECTED

emailInput.addEventListener(
    "change",
    function () {

        showSelectedFile();

    }
);


// SHOW SELECTED FILE

function showSelectedFile() {


    // NO FILE

    if (
        emailInput.files.length === 0
    ) {

        selectedFile.textContent =
            "No file selected";

        chooseButton.innerHTML =
            "↑ &nbsp; Choose File";

        return;

    }


    const file =
        emailInput.files[0];


    // CHECK FILE TYPE

    if (
        !file.name
            .toLowerCase()
            .endsWith(".eml")
    ) {

        selectedFile.textContent =
            "Please select an .eml file";

        emailInput.value = "";

        chooseButton.innerHTML =
            "↑ &nbsp; Choose File";

        return;

    }


    // SHOW FILE NAME

    selectedFile.textContent =
        "Selected: " + file.name;


    // CHANGE BUTTON

    chooseButton.innerHTML =
        "Analyze Email";

}


// DRAG OVER

uploadBox.addEventListener(
    "dragover",
    function (event) {

        event.preventDefault();

        uploadBox.classList.add(
            "dragging"
        );

    }
);


// DRAG LEAVE

uploadBox.addEventListener(
    "dragleave",
    function () {

        uploadBox.classList.remove(
            "dragging"
        );

    }
);


// DROP FILE

uploadBox.addEventListener(
    "drop",
    function (event) {

        event.preventDefault();

        uploadBox.classList.remove(
            "dragging"
        );


        const files =
            event.dataTransfer.files;


        if (files.length === 0) {

            return;

        }


        const file = files[0];


        // CHECK EML

        if (
            !file.name
                .toLowerCase()
                .endsWith(".eml")
        ) {

            selectedFile.textContent =
                "Please select an .eml file";

            return;

        }


        // SET FILE

        emailInput.files =
            files;


        selectedFile.textContent =
            "Selected: " + file.name;


        chooseButton.innerHTML =
            "Analyze Email";

    }
);