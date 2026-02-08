
function attachEventListeners() {
    console.log('Attaching event listeners');
    const nextBtn = document.getElementById('next-btn');
    const backBtn = document.getElementById('back-btn');

    console.log('nextBtn:', nextBtn);
    console.log('backBtn:', backBtn);

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            console.log('Next button clicked');
            const answer = document.querySelector('input[name="answer"]:checked');
            console.log('Answer:', answer);
            if (!answer) {
                alert("Please select an option");
                return;
            }

            const formData = new FormData(document.getElementById('question-form'));
            formData.append('action', 'next');

            console.log('Sending fetch for next');
            fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.text();
            })
            .then(html => {
                console.log('Received HTML:', html);
                if (html.includes('redirect:')) {
                    const url = html.split('redirect:')[1];
                    window.location.href = url;
                } else {
                    // Replace the question container with new content
                    document.querySelector('.questionContainer').innerHTML = html;
                    // Re-attach event listeners to the new elements
                    attachEventListeners();
                }
            })
            .catch(error => console.error('Fetch error:', error));
        });
    }

    if (backBtn) {
        backBtn.addEventListener('click', () => {
            console.log('Back button clicked');
            const formData = new FormData(document.getElementById('question-form'));
            formData.append('action', 'back');

            console.log('Sending fetch for back');
            fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.text();
            })
            .then(html => {
                console.log('Received HTML:', html);
                // Replace the question container with new content
                document.querySelector('.questionContainer').innerHTML = html;
                // Re-attach event listeners to the new elements
                attachEventListeners();
            })
            .catch(error => console.error('Fetch error:', error));
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded');
    attachEventListeners();
});


// Show Statistics
function showstats() {
    let active = document.getElementById("stats");
    let btn = document.getElementById("statsbtn");
    if (active.style.display == "none") {
        active.style.display = "block";
        btn.innerText = "Hide Statistics"; 
    }
    else if (active.style.display == "block") {
        active.style.display = "none";
        btn.innerText = "Statistics";  
    }
}

window.addEventListener("DOMContentLoaded", () => {
    // Select all flash messages
    const flashes = document.querySelectorAll(".flash");
    
    // Wait 3 seconds (3000 ms), then fade out and remove
    setTimeout(() => {
        flashes.forEach(flash => {
            flash.style.transition = "opacity 0.5s ease";
            flash.style.opacity = "0";  // fade out
            setTimeout(() => flash.remove(), 500); // remove after fade
        });
    }, 3000);
});



function hidestats() {
    let active = document.getElementById("stats");
    let btn = document.getElementById("statsbtn");

    if (active.style.display == "block") {
        active.style.display = "none";
        btn.innerText = "Show Test Statics";  
    }
}


  function showLoading() {
    document.getElementById("loading").style.display = "block";
  }

  function hideLoading() {
    document.getElementById("loading").style.display = "none";
  }

window.addEventListener("DOMContentLoaded", () => {
    // Select all flash messages
    const flashes = document.querySelectorAll(".flash");
    
    // Wait 3 seconds (3000 ms), then fade out and remove
    setTimeout(() => {
        flashes.forEach(flash => {
            flash.style.transition = "opacity 0.5s ease";
            flash.style.opacity = "0";  // fade out
            setTimeout(() => flash.remove(), 500); // remove after fade
        });
    }, 3000);
});

<<<<<<< HEAD
function loader() {
  myVar = setTimeout(showPage, 3000);
}

function showPage() {
  document.getElementById("loader").style.display = "none";
  document.getElementById("myDiv").style.display = "block";
}
=======
>>>>>>> cb5a09f (Implement AJAX for dynamic question display without full page reloads)
