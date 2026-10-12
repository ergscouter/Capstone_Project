import { useState } from 'react'
import type { FormEvent } from 'react'

export default function SignInForm() {
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [message, setMessage] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    // Replace this preview message with real authentication in the next step.
    setMessage('Account sign-in is not available in this preview yet.')
  }

  return (
    <form className="sign-in-form" onSubmit={handleSubmit}>
      <div className="form-field">
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" autoComplete="username"
          placeholder="you@example.com" required />
      </div>

      <div className="form-field">
        <label htmlFor="password">Eagle Eye password</label>
        <input id="password" name="password"
          type={passwordVisible ? 'text' : 'password'}
          autoComplete="current-password" required />
      </div>

      <label className="show-password">
        <input type="checkbox" checked={passwordVisible}
          onChange={(event) => setPasswordVisible(event.target.checked)} />
        Show password
      </label>

      <button className="sign-in-button" type="submit">Sign in</button>

      {message && <p className="form-message" role="status">{message}</p>}
    </form>
  )
}
