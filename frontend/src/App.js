import React, { Component } from 'react'
import './App.css'
import {
  BrowserRouter as Router,
  Route,
  NavLink,
  Redirect
} from 'react-router-dom'
import { observer } from 'mobx-react'
import 'bulma/css/bulma.css'

import Home from './Home'
import Help from './Help'
import Tokens from './Tokens'
import Uploads from './Uploads'
import Upload from './Upload'
import Files from './Files'
import Users from './Users'
import User from './User'
import FetchError from './FetchError'
import Fetch from './Fetch'
import DisplayAPIRequests from './APIRequests'
import store from './Store'

const App = observer(
  class App extends Component {
    constructor(props) {
      super(props)
      this.state = {
        redirectTo: null
      }
    }
    componentWillMount() {
      Fetch('/api/auth/', { credentials: 'same-origin' }).then(r => {
        if (r.status === 200) {
          if (store.fetchError) {
            store.fetchError = null
          }
          r.json().then(response => {
            if (response.user) {
              store.currentUser = response.user
              store.signOutUrl = response.sign_out_url
              // XXX do we need to remove the ?signedin=True in the query string?
            }
          })
        } else {
          store.fetchError = r
        }
      })
    }

    signIn = event => {
      event.preventDefault()
      fetch('/api/auth/', { credentials: 'same-origin' })
        .then(r => r.json())
        .then(response => {
          if (response.sign_in_url) {
            let signInUrl = response.sign_in_url
            // When doing local development, the Django runserver is
            // running at 'http://web:8000' as far as the React dev
            // server is concerned. That doesn't work outside Docker
            // (i.e on the host) so we'll replace this.
            signInUrl = signInUrl.replace(
              'http://web:8000',
              'http://localhost:8000'
            )
            document.location.href = signInUrl
          } else {
            store.currentUser = response.user
            store.signOutUrl = response.sign_out_url
          }
        })
    }

    signOut = event => {
      event.preventDefault()
      Fetch(store.signOutUrl, {
        method: 'POST',
        credentials: 'same-origin'
      }).then(r => {
        console.log('SIGNED OUT:')
        console.log(r)
      })
    }

    render() {
      if (this.state.redirectTo) {
        return <Redirect to={this.state.redirectTo} />
      }
      return (
        <Router>
          <div>
            <nav className="nav has-shadow" id="top">
              <div className="container">
                <div className="nav-left">
                  <a className="nav-item" href="/">
                    Mozilla Symbol Server
                  </a>
                </div>
                <span className="nav-toggle">
                  <span />
                  <span />
                  <span />
                </span>
                <div className="nav-right nav-menu">
                  <NavLink
                    to="/"
                    exact
                    className="nav-item is-tab"
                    activeClassName="is-active"
                  >
                    Home
                  </NavLink>
                  {store.currentUser && store.currentUser.is_superuser
                    ? <NavLink
                        to="/users"
                        className="nav-item is-tab"
                        activeClassName="is-active"
                      >
                        User Management
                      </NavLink>
                    : null}
                  <NavLink
                    to="/tokens"
                    className="nav-item is-tab"
                    activeClassName="is-active"
                  >
                    API Tokens
                  </NavLink>
                  <NavLink
                    to="/uploads"
                    className="nav-item is-tab"
                    activeClassName="is-active"
                  >
                    Uploads
                  </NavLink>
                  <NavLink
                    to="/help"
                    className="nav-item is-tab"
                    activeClassName="is-active"
                  >
                    Help
                  </NavLink>
                  <span className="nav-item">
                    {store.currentUser
                      ? <a
                          onClick={this.signOut}
                          className="button is-info"
                          title={`Signed in as ${store.currentUser.email}`}
                        >
                          Sign Out
                        </a>
                      : <a onClick={this.signIn} className="button is-info">
                          Sign In
                        </a>}
                  </span>
                </div>
              </div>
            </nav>
            <section className="section">
              <div className="container">
                <FetchError error={store.fetchError} />
                <Route path="/" exact component={Home} />
                <Route path="/help" component={Help} />
                <Route path="/tokens" component={Tokens} />
                <Route path="/uploads/files" exact component={Files} />
                <Route path="/uploads/upload/:id" component={Upload} />
                <Route path="/uploads" exact component={Uploads} />
                <Route path="/users/:id" component={User} />
                <Route path="/users" exact component={Users} />

                <DisplayAPIRequests />
              </div>
            </section>
            <footer className="footer">
              <div className="container">
                <div className="content has-text-centered">
                  <p>
                    <strong>The Mozilla Symbol Server</strong>
                    <br />
                    Powered by{' '}
                    <a
                      href="https://github.com/mozilla-services/tecken"
                      rel="noopener noreferrer"
                    >
                      Tecken
                    </a>
                    {' • '}
                    <a
                      href="https://tecken.readthedocs.io"
                      rel="noopener noreferrer"
                    >
                      Documentation
                    </a>
                  </p>
                </div>
              </div>
            </footer>
          </div>
        </Router>
      )
    }
  }
)

export default App
