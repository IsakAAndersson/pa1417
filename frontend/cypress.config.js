module.exports = {
  e2e: {
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    baseUrl: 'http://localhost:3000',  // Lägg till baseUrl här
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',  // Specifika filtyper för dina tester
  },

  component: {
    devServer: {
      framework: "create-react-app",
      bundler: "webpack",
    },
  },
};
