import './App.css'

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">Career Mentor Companion</div>
        <nav className="nav-links">
          <a href="#interview">Interview</a>
          <a href="#dashboard">Dashboard</a>
          <a href="#blog">Blog</a>
          <a href="#about">About us</a>
          <a href="#signin" className="sign-in-link">
            Sign In
          </a>
        </nav>
      </header>

      <main>
        <section className="hero">
          <div>
            <p className="eyebrow">Smart career support</p>
            <h1>Prepare for interviews with confidence.</h1>
            <p className="hero-text">
              A simple platform to practice, track progress, and grow your career.
            </p>
            <div className="hero-actions">
              <a href="#interview" className="cta-button primary">
                Start Interview
              </a>
              <a href="#signin" className="cta-button secondary">
                Sign In
              </a>
            </div>
          </div>
          <div className="hero-card">
            <h2>What you can do</h2>
            <ul>
              <li>Practice mock interviews</li>
              <li>Track weak areas</li>
              <li>Read helpful career tips</li>
            </ul>
          </div>
        </section>

        <section id="interview" className="section-card">
          <h2>Interview</h2>
          <p>Practice real interview questions and improve your answers.</p>
        </section>

        <section id="dashboard" className="section-card">
          <h2>Dashboard</h2>
          <p>View your progress, sessions, and performance in one place.</p>
        </section>

        <section id="blog" className="section-card">
          <h2>Blog</h2>
          <p>Read short articles on interviews, resumes, and career growth.</p>
        </section>

        <section id="about" className="section-card">
          <h2>About us</h2>
          <p>We build supportive tools to help students prepare for their next step.</p>
        </section>

        <section id="signin" className="section-card signin-card">
          <h2>Sign In</h2>
          <p>Use your account details to access your interview dashboard and progress.</p>
          <form className="signin-form">
            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input id="email" name="email" type="email" placeholder="you@example.com" required />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input id="password" name="password" type="password" placeholder="Enter your password" required />
            </div>
            <button type="submit" className="signin-button">
              Sign In
            </button>
          </form>
        </section>
      </main>

      <footer className="footer">© 2026 Career Mentor Companion</footer>
    </div>
  )
}

export default App
