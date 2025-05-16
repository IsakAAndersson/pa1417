describe('Todo Item Manipulation (Requirement 8)', () => {
  // Define variables we need across tests
  let uid; // User ID
  let taskId; // Task ID
  let name; // User name
  let email; // User email
  
  before(function () {
    // Create a test user from fixture
    cy.fixture('user.json')
      .then((user) => {
        cy.request({
          method: 'POST',
          url: 'http://localhost:5000/users/create',
          form: true,
          body: user
        }).then((response) => {
          uid = response.body._id.$oid;
          name = user.firstName + ' ' + user.lastName;
          email = user.email;
          
          // Create a task for this user
          cy.request({
            method: 'POST',
            url: 'http://localhost:5000/tasks/create',
            form: true,
            body: {
              userid: uid,
              title: "Test Task",
              description: "Task for testing todos",
              url: "dQw4w9WgXcQ", // Rick Roll video key
              todos: "Watch video"
            }
          }).then((taskResponse) => {
            // Store the first task ID
            taskId = taskResponse.body[0]._id.$oid;

            
          });
        });
      });
  });
  
  beforeEach(function () {
    // Login before each test (Precondition: The user is authenticated)
    cy.visit('http://localhost:3000');
    cy.contains('div', 'Email Address')
      .find('input[type=text]')
      .type(email);
    cy.get('form').submit();
    
    // Wait for login to complete and verify
    cy.contains('h1', `Your tasks, ${name}`).should('be.visible');
  
    // Wait for tasks to be loaded and verify there's at least one task
  cy.get('.container-element').should('be.visible').should('have.length.at.least', 1);
  
  // Force wait a bit to ensure UI is fully loaded and stable
  cy.wait(500);

    // Open the task details by clicking on the first task
    // (Precondition: has at least one task associated to their account)
    cy.get('.container-element').first().click();
    
    // Verify the popup is open (Precondition: views this task in detail view mode)
    cy.get('.popup-inner').should('be.visible');
  });
  
  // R8UC1: Add a new todo item
  it('should add a new todo item to a task (R8UC1)', () => {
    const todoText = 'New test todo item ' + Date.now();
    
    // Main Success Scenario step 1: The user enters a description of a todo item into an empty input form field
    cy.get('.todo-list li:last-child form input[type="text"]')
      .type(todoText);
    
    // Main Success Scenario step 2: If the description is not empty and the user presses "Add", the system creates a new todo item
    cy.get('.todo-list li:last-child form')
      .submit();
    
    // End Condition: The new (active) todo item with the given description is appended to the bottom of the list of existing todo items
    cy.get('.todo-list .todo-item').last()
      .find('.editable').should('contain.text', todoText);
    
    // Check that the todo item is active (not struck through)
    cy.get('.todo-list .todo-item').last()
      .find('.checker').should('have.class', 'unchecked')
      .and('not.have.class', 'checked');
      
    // Verify the input field is cleared
    cy.get('.todo-list li:last-child form input[type="text"]')
      .should('have.value', '');
  });
  
  // Alternative Scenario 2.b for R8UC1: Empty description keeps Add button disabled
  it('should keep the Add button disabled when description is empty (R8UC1 Alternative)', () => {
    // Get the add button and verify it's disabled initially
    cy.get('.todo-list li:last-child form button[type="submit"]')
      .should('be.disabled');
      
    // Type something then delete it
    cy.get('.todo-list li:last-child form input[type="text"]')
      .type('Something')
      .clear();
      
    // Verify the button is disabled again
    cy.get('.todo-list li:last-child form button[type="submit"]')
      .should('be.disabled');
  });
  
  // R8UC2: Toggle an existing todo item status
  it('should toggle the status of a todo item (R8UC2)', () => {
    // Get the first todo item
    cy.get('.todo-list .todo-item').first().as('firstTodo');
    
    // Check initial state
    cy.get('@firstTodo').find('.checker').then($checker => {
      const isInitiallyChecked = $checker.hasClass('checked');
      
      // Main Success Scenario step 1: The user clicks on the icon in front of the description of the todo item
      cy.get('@firstTodo').find('.checker').click();
      
      if (isInitiallyChecked) {
        // Alternative Scenario 2.b: If the todo item was previously done, it is set to active
        cy.get('@firstTodo').find('.checker').should('have.class', 'unchecked');
        cy.get('@firstTodo').find('.checker').should('not.have.class', 'checked');
        // End Condition: The toggled todo item is not struck through anymore
        cy.get('@firstTodo').find('.editable').should('not.have.css', 'text-decoration', 'line-through');
      } else {
        // Main Success Scenario step 2: If the todo item was previously active, it is set to done
        cy.get('@firstTodo').find('.checker').should('have.class', 'checked');
        cy.get('@firstTodo').find('.checker').should('not.have.class', 'unchecked');
        // End Condition: The toggled todo item is struck through
        cy.get('@firstTodo').find('.editable').should('have.css', 'text-decoration').and('include', 'line-through');
      }
    });
  });
  
  // R8UC3: Delete an existing todo item
  it('should delete a todo item (R8UC3)', () => {
    // Store the todo items before deletion
    cy.get('.todo-list .todo-item').then(($todos) => {
      const initialCount = $todos.length;
      
      // Get text of the first todo for verification
      const deletedText = $todos.first().find('.editable').text();
      
      // Main Success Scenario step 1: If user clicks on the x symbol behind the description of the todo item, the todo item is deleted
      cy.get('.todo-list .todo-item').first()
        .find('.remover').click();
      
      // End Condition: The todo item is removed from the todo list
      cy.get('.todo-list .todo-item').should('have.length', initialCount - 1);
      
      // Verify the deleted todo text is no longer present
      cy.get('.todo-list .todo-item').each(($item) => {
        expect($item.find('.editable').text()).not.to.eq(deletedText);
      });
    });
  });
  
  afterEach(() => {
    // Close the popup only if it exists
    cy.get('body').then($body => {
      if ($body.find('.popup-inner .close-btn').length > 0) {
        cy.get('.popup-inner .close-btn').click({ force: true });
        cy.get('.popup').should('not.exist');
      }
    });
  });
  
  after(function () {
    
    // Cleanup - delete the user which will also delete associated tasks
    if (uid) {
      cy.request({
        method: 'DELETE',
        url: `http://localhost:5000/users/${uid}`
      });
    }
  });
});