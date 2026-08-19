import {
  createContext,
  useContext,
  useEffect,
  useState,
} from 'react';

import {
  apiGetCurrentUser,
  apiLogin,
  apiLogout,
} from '../api/api.js';


// ==================================================
// Context
// ==================================================

const AuthContext = createContext(null);


// ==================================================
// Provider
// ==================================================

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  /*
   * We need to distinguish between:

   * 1. We haven't checked the Django session yet.
   * 2. We checked and the user is authenticated.
   * 3. We checked and the user is a guest.
   */
  const [loading, setLoading] = useState(true);


  // ------------------------------------------------
  // Check existing Django session
  // ------------------------------------------------

  useEffect(() => {
    async function checkAuthentication() {
      try {
        const data = await apiGetCurrentUser();

        if (data.authenticated) {
          setUser(data.user);
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error(
          'Failed to check authentication:',
          error
        );

        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    checkAuthentication();
  }, []);


  // ------------------------------------------------
  // Login
  // ------------------------------------------------

  async function login(username, password) {
    const data = await apiLogin(
      username,
      password
    );

    /*
     * The actual session is stored by Django.
     *
     * We only keep the user's basic information
     * in React state.
     */
    setUser(data.user);

    return data;
  }


  // ------------------------------------------------
  // Logout
  // ------------------------------------------------

  async function logout() {
    try {
      await apiLogout();
    } finally {
      /*
       * Whether the request succeeds or fails,
       * React should no longer consider the user
       * authenticated locally.
       */
      setUser(null);
    }
  }


  // ------------------------------------------------
  // Context value
  // ------------------------------------------------

  const value = {
    user,
    loading,
    isAuthenticated: user !== null,
    login,
    logout
  };


  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}


// ==================================================
// Hook
// ==================================================

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      'useAuth must be used inside an AuthProvider'
    );
  }

  return context;
}