import SignInForm from './components/SignInForm'

export default function App() {
  return (
    <main className="sign-in-page">
      <section className="account-card" aria-labelledby="sign-in-heading">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">EE</span>
          <span>Eagle Eye</span>
        </div>
        <p className="preview-label">Student capstone · Team 1 A</p>
        <h1 id="sign-in-heading">Welcome back</h1>
        <p className="intro">
          Sign in to save your class schedule, favorite places, and parking preferences.
        </p>
        <SignInForm />
        <p className="preview-note">
          Screen preview only. Account sign-in is not available yet.
        </p>
      </section>
    </main>
  )
}
