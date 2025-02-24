// Import required modules
const fs = require('fs');
const path = require('path');

// Function to append content to RAG.txt
function appendToReadme(content) {
  const readmePath = path.join(__dirname, '.cursor', 'rules', 'RAG.txt');
  
  // Ensure the directory exists
  const dirPath = path.dirname(readmePath);
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
  
  fs.appendFileSync(readmePath, content + '\n\n');
  console.log('Content added to .cursor/rules/RAG.txt');
}

// Main agent function
async function captureConversation() {
  // Listen for Cursor AI composer events
  cursor.on('composerQuestion', (question) => {
    const timestamp = new Date().toISOString();
    appendToReadme(`# Question (${timestamp}):\n${question}`);
  });

  cursor.on('composerResponse', (response) => {
    const timestamp = new Date().toISOString();
    appendToReadme(`# Response (${timestamp}):\n${response}`);
  });
  
  console.log('Cursor AI conversation logger started. Recording to .cursor/rules/RAG.txt');
}

// Run the agent
captureConversation();