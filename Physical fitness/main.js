document.addEventListener('DOMContentLoaded', function () {
  const loginForm = document.querySelector('form'); // Assumes the login inputs are within a <form>
if (loginForm) {
    loginForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      const email = loginForm.querySelector('input[aria-label="Email"]').value.trim();
      const password = loginForm.querySelector('input[aria-label="Password"]').value;
      if (!email || !password) {
        alert('Please enter both email and password.');
        return;
      }try {
        const response = await fetch('https://your-backend-api-url/api/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ email, password })
        });
const data = await response.json();

        if (response.ok) {
          window.location.href = data.redirectUrl || '/dashboard';
        } else {          alert(data.message || 'Login failed.');
        }
      } catch (error) {
        alert('Something went wrong. Please try again.');
      }
    });
  }
});
2.Workouts Form Handling (feedback.html + JS snippet)
document.addEventListener('DOMContentLoaded', () => {
  const workoutForm = document.getElementById('workout-form');
  const workoutList = document.getElementById('workout-list');
let workouts = JSON.parse(localStorage.getItem('workouts')) || [];
function renderWorkouts() {
    workoutList.innerHTML = '';
    workouts.forEach((workout, index) => {
      const li = document.createElement('li');
      li.textContent = `${workout.type} - ${workout.duration} mins`;
      const delBtn = document.createElement('button');
      delBtn.textContent = 'Delete';
      delBtn.onclick = () => {
        workouts.splice(index, 1);
        localStorage.setItem('workouts', JSON.stringify(workouts));
        renderWorkouts();
      };
      li.appendChild(delBtn);
      workoutList.appendChild(li);
    });
  }
  workoutForm.onsubmit = (e) => {
    e.preventDefault();
    const type = document.getElementById('workout-type').value.trim();
    const duration = document.getElementById('workout-duration').value;
    workouts.push({ type, duration });
    localStorage.setItem('workouts', JSON.stringify(workouts));
    renderWorkouts();
    workoutForm.reset();
  };
renderWorkouts();
  const feedbackForm = document.getElementById('feedback-form');
  feedbackForm.onsubmit = (e) => {
    e.preventDefault();
    const feedback = document.getElementById('workout-feedback').value.trim();
    // In a real app, send feedback to backend with fetch()/AJAX here
    alert('Feedback submitted: ' + feedback);
    feedbackForm.reset();
  };
});
3.Nutrtion Diet  Form Handling (support.html + JS snippet)
document.addEventListener('DOMContentLoaded', () => {
  const nutritionForm = document.getElementById('nutrition-form');
  const nutritionList = document.getElementById('nutrition-list');
  let diets = JSON.parse(localStorage.getItem('diets')) || [];
 function renderDietLog() {
    nutritionList.innerHTML = '';
    diets.forEach((diet, idx) => {
      const li = document.createElement('li');
      li.textContent =
        `${diet.date}: ${diet.calories}kcal, ${diet.protein}g protein, ${diet.carbs}g carbs, ${diet.fats}g fats, Pref: ${diet.pref}`;
      const delBtn = document.createElement('button');
      delBtn.textContent = 'Delete';
      delBtn.onclick = () => {
        diets.splice(idx, 1);
        localStorage.setItem('diets', JSON.stringify(diets));
        renderDietLog();
      };
      li.appendChild(delBtn);
      nutritionList.appendChild(li);
    });
  }
 nutritionForm.onsubmit = (e) => {
    e.preventDefault();
    const date      = document.getElementById('nutrition-date').value;
    const calories  = document.getElementById('nutrition-calories').value;
    const protein   = document.getElementById('nutrition-protein').value;
    const carbs     = document.getElementById('nutrition-carbs').value;
    const fats      = document.getElementById('nutrition-fats').value;
    const pref      = document.getElementById('nutrition-pref').value.trim();

    diets.push({ date, calories, protein, carbs, fats, pref });
    localStorage.setItem('diets', JSON.stringify(diets));
    renderDietLog();
    nutritionForm.reset();
  };
  renderDietLog();
})
