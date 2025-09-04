/**
 * AI Hub Client for FCHR Voice Assistant Integration
 *
 * This module provides a JavaScript client for integrating the FCHR voice assistant
 * with the AI Hub system for idea collection and management.
 */

class AIHubClient {
  constructor(baseUrl = 'http://localhost:8000/api/v1', apiKey = null) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.timeout = 30000; // 30 seconds
  }

  /**
   * Get headers for API requests
   */
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    return headers;
  }

  /**
   * Make API request with error handling
   */
  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: this.getHeaders(),
      timeout: this.timeout,
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`AI Hub API request failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Find or create user
   */
  async resolveUser(userName, userEmail = null, userRole = null, userDepartment = null) {
    try {
      // First, try to find existing user
      if (userEmail) {
        const existingUsers = await this.makeRequest(`/users?email=${encodeURIComponent(userEmail)}`);
        if (existingUsers.length > 0) {
          return existingUsers[0];
        }
      }

      // Create new user if not found
      const userData = {
        full_name: userName,
        email: userEmail,
        role: userRole || 'developer',
        department: userDepartment || 'engineering'
      };

      const newUser = await this.makeRequest('/users', {
        method: 'POST',
        body: JSON.stringify(userData)
      });

      return newUser;
    } catch (error) {
      console.error('Failed to resolve user:', error);
      throw new Error('Unable to identify user in the system');
    }
  }

  /**
   * Submit an idea
   */
  async submitIdea(rawInput, userName, userEmail = null, userRole = null, userDepartment = null) {
    try {
      const ideaData = {
        raw_input: rawInput,
        user_name: userName,
        user_email: userEmail,
        user_role: userRole,
        user_department: userDepartment
      };

      const idea = await this.makeRequest('/ideas', {
        method: 'POST',
        body: JSON.stringify(ideaData)
      });

      return idea;
    } catch (error) {
      console.error('Failed to submit idea:', error);
      throw new Error('Unable to submit idea to the system');
    }
  }

  /**
   * Check for duplicate ideas
   */
  async checkDuplicates(ideaId) {
    try {
      const duplicates = await this.makeRequest(`/ideas/${ideaId}/duplicates`);
      return duplicates;
    } catch (error) {
      console.error('Failed to check duplicates:', error);
      return [];
    }
  }

  /**
   * Get idea status
   */
  async getIdeaStatus(ideaId) {
    try {
      const idea = await this.makeRequest(`/ideas/${ideaId}`);
      return idea;
    } catch (error) {
      console.error('Failed to get idea status:', error);
      throw new Error('Unable to retrieve idea status');
    }
  }

  /**
   * Get user's ideas
   */
  async getUserIdeas(userId, status = null) {
    try {
      let endpoint = `/ideas?author_id=${userId}`;
      if (status) {
        endpoint += `&status=${status}`;
      }

      const response = await this.makeRequest(endpoint);
      return response.items || [];
    } catch (error) {
      console.error('Failed to get user ideas:', error);
      return [];
    }
  }

  /**
   * Get idea history/audit trail
   */
  async getIdeaHistory(ideaId) {
    try {
      const history = await this.makeRequest(`/ideas/${ideaId}/history`);
      return history.history || [];
    } catch (error) {
      console.error('Failed to get idea history:', error);
      return [];
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      await this.makeRequest('/health');
      return true;
    } catch (error) {
      return false;
    }
  }
}

/**
 * Voice Assistant Integration Helper
 */
class VoiceAssistantHelper {
  constructor(aiHubClient) {
    this.aiHub = aiHubClient;
    this.currentUser = null;
    this.lastIdea = null;
  }

  /**
   * Process voice command for idea submission
   */
  async processIdeaSubmission(voiceText, userContext) {
    try {
      // Extract user information from context
      const { name, email, role, department } = userContext;

      // Resolve user
      this.currentUser = await this.aiHub.resolveUser(name, email, role, department);

      // Submit idea
      this.lastIdea = await this.aiHub.submitIdea(voiceText, name, email, role, department);

      // Check for duplicates
      const duplicates = await this.aiHub.checkDuplicates(this.lastIdea.id);

      return {
        success: true,
        idea: this.lastIdea,
        duplicates: duplicates,
        user: this.currentUser
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Process status inquiry
   */
  async processStatusInquiry(userContext) {
    try {
      if (!this.currentUser) {
        this.currentUser = await this.aiHub.resolveUser(
          userContext.name,
          userContext.email
        );
      }

      const ideas = await this.aiHub.getUserIdeas(this.currentUser.id);

      return {
        success: true,
        user: this.currentUser,
        ideas: ideas,
        totalCount: ideas.length
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Generate response text for voice assistant
   */
  generateResponse(result, intent) {
    if (!result.success) {
      return `I'm sorry, I encountered an error: ${result.error}. Please try again later.`;
    }

    switch (intent) {
      case 'submit_idea':
        return this.generateIdeaSubmissionResponse(result);

      case 'check_status':
        return this.generateStatusResponse(result);

      case 'check_duplicates':
        return this.generateDuplicatesResponse(result);

      default:
        return "I've processed your request successfully.";
    }
  }

  generateIdeaSubmissionResponse(result) {
    const { idea, duplicates } = result;

    let response = `✅ Idea submitted successfully!

📋 Details:
• ID: #${idea.id}
• Title: ${idea.title}
• Status: ${idea.status.replace('_', ' ').toUpperCase()}

📊 Analysis:
• Category: ${idea.category || 'To be determined'}
• Readiness: ${idea.readiness_level || 'To be assessed'}

📧 Next Steps:
• Analyst review within 5 days
• Email updates will be sent to ${result.user.email || 'your registered email'}
• Track progress at: /ideas/${idea.id}
`;

    if (duplicates && duplicates.length > 0) {
      const topDuplicate = duplicates[0];
      const similarityPercent = Math.round(topDuplicate.similarity_score * 100);

      response += `

🔍 Similar Idea Found:
• Match: ${similarityPercent}% similar
• Title: "${topDuplicate.title}"
• Status: ${topDuplicate.status}

Would you like to link this as an improvement or proceed separately?`;
    }

    return response;
  }

  generateStatusResponse(result) {
    const { ideas, totalCount } = result;

    if (totalCount === 0) {
      return "You don't have any active ideas in the system. Would you like to submit a new idea?";
    }

    let response = `📋 You have ${totalCount} idea${totalCount > 1 ? 's' : ''} in the system:

`;

    ideas.slice(0, 3).forEach((idea, index) => {
      response += `${index + 1}. **${idea.title}** (ID: #${idea.id})
   Status: ${idea.status.replace('_', ' ').toUpperCase()}
   Created: ${new Date(idea.created_at).toLocaleDateString()}

`;
    });

    if (totalCount > 3) {
      response += `\n... and ${totalCount - 3} more ideas.`;
    }

    response += `\nWould you like me to check the details of any specific idea?`;

    return response;
  }

  generateDuplicatesResponse(result) {
    const { duplicates } = result;

    if (!duplicates || duplicates.length === 0) {
      return "No similar ideas found in the system.";
    }

    let response = `🔍 Found ${duplicates.length} similar idea${duplicates.length > 1 ? 's' : ''}:

`;

    duplicates.slice(0, 3).forEach((dup, index) => {
      const similarityPercent = Math.round(dup.similarity_score * 100);
      response += `${index + 1}. **${dup.title}** (${similarityPercent}% match)
   Status: ${dup.status.replace('_', ' ').toUpperCase()}

`;
    });

    return response;
  }
}

// Export for use in FCHR voice assistant
module.exports = {
  AIHubClient,
  VoiceAssistantHelper
};

// Example usage:
/*
const aiHub = new AIHubClient('http://localhost:8000/api/v1');
const helper = new VoiceAssistantHelper(aiHub);

// Submit an idea
const result = await helper.processIdeaSubmission(
  "I think we should add dark mode to the dashboard",
  { name: "John Doe", email: "john@company.com", role: "developer", department: "engineering" }
);

const response = helper.generateResponse(result, 'submit_idea');
console.log(response);
*/
