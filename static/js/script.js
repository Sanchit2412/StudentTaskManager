document.addEventListener("DOMContentLoaded", function () {

    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {

        setTimeout(function () {

            const closeButton = alert.querySelector(".btn-close");

            if (closeButton) {
                closeButton.click();
            }

        }, 4000);

    });

});
document.addEventListener("DOMContentLoaded", function () {

    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {

        setTimeout(function () {

            const closeButton = alert.querySelector(".btn-close");

            if (closeButton) {
                closeButton.click();
            }

        }, 4000);

    });


    const progressBar = document.querySelector("[data-progress]");

    if (progressBar) {

        const progress = progressBar.getAttribute("data-progress");

        progressBar.style.width = progress + "%";

    }

});