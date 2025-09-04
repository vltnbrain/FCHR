# AI Hub Idea Handling Guide for FCHR Voice Assistant

## Overview
This guide outlines how the FCHR voice assistant should integrate with the AI Hub system for collecting, processing, and routing user ideas through the role-based approval workflow.

## Integration Architecture

```
FCHR Voice Assistant → AI Hub REST API → PostgreSQL + pgvector
                              ↓
                         Email Notifications → Role-based Routing
                              ↓
                    SLA Timers & Escalations
```

## Conversation Flow

### 1. User Identification & Context
**Goal**: Identify the user and provide personalized context

**Steps**:
1. Ask for user's full name if not known
2. Query AI Hub API: `GET /api/v1/users?email={email}` or `POST /api/v1/users` to create
3. If returning user, check last interaction: `GET /api/v1/users/{id}`
4. Provide recap: "Welcome back {name}! Your last interaction was {N} days ago regarding {last_idea_title}. How can I help you today?"

**API Calls**:
```javascript
// Check if user exists
const userResponse = await fetch(`${AI_HUB_URL}/api/v1/users?email=${userEmail}`);
const users = await userResponse.json();

// Create user if doesn't exist
if (users.length === 0) {
  const createResponse = await fetch(`${AI_HUB_URL}/api/v1/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      full_name: userName,
      email: userEmail,
      role: inferredRole, // 'developer', 'analyst', etc.
      department: inferredDepartment
    })
  });
}
```

### 2. Idea Capture
**Goal**: Capture the user's idea with context

**Prompt Template**:
```
I'd like to help you submit an idea to our AI Hub. Could you tell me about your idea?

[User responds with idea]

Thanks! Let me capture that. Based on what you've shared, this seems like a {category} idea for the {department} team.

Should I proceed with submitting this to our idea pipeline?
```

**API Call**:
```javascript
const ideaResponse = await fetch(`${AI_HUB_URL}/api/v1/ideas`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    raw_input: userIdeaText,
    user_name: userName,
    user_email: userEmail,
    user_role: userRole,
    user_department: userDepartment
  })
});

const idea = await ideaResponse.json();
```

### 3. Duplicate Detection & Structuring
**Goal**: Check for similar ideas and provide feedback

**Response Template**:
```
✅ Your idea has been submitted successfully!

📊 Analysis Results:
- Category: {category}
- Recommended Team: {team}
- Readiness Level: {level}

🔍 Similarity Check:
{duplicate_results}

📧 Next Steps:
- Analyst will review within 5 days
- You'll receive email updates at {userEmail}
- Track progress at: {dashboardUrl}/ideas/{ideaId}
```

**Duplicate Handling**:
```javascript
// Check for duplicates
const duplicatesResponse = await fetch(`${AI_HUB_URL}/api/v1/ideas/${idea.id}/duplicates`);
const duplicates = await duplicatesResponse.json();

if (duplicates.length > 0) {
  const topDuplicate = duplicates[0];
  if (topDuplicate.similarity_score >= 0.8) {
    response = `I found a very similar idea (${topDuplicate.similarity_score * 100}% match): "${topDuplicate.title}". Would you like to link your idea as an improvement to this existing one, or proceed as a separate idea?`;
  }
}
```

### 4. Status Updates & Follow-ups
**Goal**: Keep user informed of progress

**Commands**:
- "What's the status of my idea?"
- "Check on idea #123"
- "Any updates on my submissions?"

**API Call**:
```javascript
const statusResponse = await fetch(`${AI_HUB_URL}/api/v1/ideas?author_id=${userId}&status=pending`);
const ideas = await statusResponse.json();

response = `You have ${ideas.length} active ideas. Here's the latest:`;
// Format and present idea statuses
```

## API Integration Details

### Authentication
```javascript
// For production, use proper authentication
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${process.env.AI_HUB_API_KEY}`
};
```

### Error Handling
```javascript
try {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  return await response.json();
} catch (error) {
  // Fallback to voice response
  return "I'm having trouble connecting to our idea system right now. Please try again later or contact support.";
}
```

## Voice Command Patterns

### Intent Recognition
```
"I have an idea" → Start idea capture flow
"Check my ideas" → List user's ideas
"Status of idea" → Get specific idea status
"Similar to X" → Check for duplicates
```

### Slot Extraction
```
User: "I work in engineering and have an idea for a new dashboard"
→ department: "engineering"
→ category: "feature"
→ context: "dashboard"

User: "This is similar to the login issue we discussed last month"
→ intent: "duplicate_check"
→ reference: "login issue"
```

## Response Templates

### Success Submission
```
🎉 **Idea Submitted Successfully!**

**ID**: #{ideaId}
**Title**: {generatedTitle}
**Status**: Analyst Review (5-day SLA)

You'll receive an email when the analyst reviews it. You can also check the status anytime by asking me "What's the status of idea #{ideaId}?"
```

### Duplicate Found
```
🔍 **Similar Idea Detected**

I found an existing idea that matches yours **{similarity}%**:
**"{existingTitle}"** by {authorName}

**Options**:
1. Link as improvement to existing idea
2. Proceed as separate idea
3. Cancel submission

What would you like to do?
```

### Status Check
```
📋 **Idea Status Update**

**Idea #{ideaId}**: {title}
**Current Status**: {status}
**Last Updated**: {lastUpdate}

**Next Steps**: {nextStepDescription}
**SLA Status**: {slaStatus} (Due: {dueDate})
```

## Configuration

### Environment Variables
```bash
AI_HUB_BASE_URL=http://localhost:8000/api/v1
AI_HUB_API_KEY=your-api-key
VOICE_ASSISTANT_TIMEOUT=30000
```

### Integration Points
- **Webhook URL**: For real-time status updates
- **Health Check**: Monitor AI Hub availability
- **Fallback Mode**: Graceful degradation when API is down

## Testing Scenarios

1. **New User Flow**: Complete user creation + idea submission
2. **Returning User**: Context recap + status update
3. **Duplicate Detection**: High/low similarity responses
4. **Error Handling**: API failures, timeouts, invalid data
5. **Multi-turn Conversation**: Follow-up questions and clarifications

## Monitoring & Analytics

Track:
- Idea submission success rate
- User engagement metrics
- Duplicate detection accuracy
- SLA compliance rates
- Voice command recognition accuracy

## Future Enhancements

- Voice-based duplicate confirmation
- Multi-language support
- Integration with project management tools
- Advanced intent recognition with ML
- Proactive idea suggestions based on user history
