export interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'active' | 'complete';
  avatar: string;
  description: string;
  currentAction?: string;
}

export interface CrisisEvent {
  id: string;
  timestamp: string;
  type: 'detection' | 'sentiment' | 'fact-check' | 'draft' | 'published';
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export const initialAgents: Agent[] = [
  {
    id: 'ear-to-ground',
    name: 'Ear to the Ground',
    status: 'idle',
    avatar: '🛰️',
    description: 'Social Media Monitoring Agent',
    currentAction: 'Scanning social channels...'
  },
  {
    id: 'sentiment-analyzer',
    name: 'Sentiment Analyzer',
    status: 'idle',
    avatar: '📊',
    description: 'Public Opinion Analysis Agent',
  },
  {
    id: 'fact-checker',
    name: 'Fact Checker',
    status: 'idle',
    avatar: '🔍',
    description: 'Information Verification Agent',
  },
  {
    id: 'press-secretary',
    name: 'Press Secretary',
    status: 'idle',
    avatar: '📝',
    description: 'Response Generation Agent',
  }
];

export const crisisData = {
  viralTweet: {
    author: '@PopBase',
    handle: 'Pop Base',
    timestamp: 'Jul 17, 2025',
    content: 'Coldplay accidentally exposed an alleged affair between Astronomer CEO Andy Byron and his colleague Kristin Cabot at one of their recent concerts.',
    likes: '152.7M',
    retweets: '45.2K',
    replies: '18.9K',
    videoThumbnail: '/popbase-tweet.jpg',
    videoThumbnail: './popbase-tweet.png',
    videoThumbnail: '/src/assets/popbase-tweet.png',
    videoDuration: '0:14',
    views: '152.7M Views'
  },
  
  sentimentData: {
    overall: 'Highly Negative',
    score: -0.78,
    breakdown: {
      anger: 45,
      disappointment: 32,
      concern: 18,
      neutral: 5
    },
    trendingTerms: ['boycott', 'disappointed', 'unprofessional', 'resign', 'accountability', 'leadership']
  },

  policySnippet: {
    title: 'Crisis Response Protocol - Section 4.2',
    content: `In cases of executive misconduct allegations:
    
1. Acknowledge the situation promptly
2. Express commitment to company values
3. Indicate investigation will be conducted
4. Avoid admitting fault until facts are established
5. Emphasize continued service to customers

Tone: Professional, empathetic, transparent
Timeline: Initial response within 2 hours`
  },

  draftStatement: `We are aware of the video circulating on social media involving our CEO Andy Byron. We take all concerns about leadership conduct seriously and are committed to upholding the highest standards of professionalism.

We are currently reviewing the situation and will take appropriate action based on our findings. Astronomer remains dedicated to serving our customers and maintaining the trust they place in us.

We will provide updates as appropriate.`
};

export const timelineEvents: CrisisEvent[] = [
  {
    id: '1',
    timestamp: '09:15:23',
    type: 'detection',
    title: 'Crisis Detected',
    description: 'Viral content flagged by monitoring systems',
    severity: 'critical'
  },
  {
    id: '2',
    timestamp: '09:15:45',
    type: 'sentiment',
    title: 'Sentiment Analysis Complete',
    description: 'Public opinion trending highly negative',
    severity: 'high'
  },
  {
    id: '3',
    timestamp: '09:16:12',
    title: 'Policy Retrieved',
    type: 'fact-check',
    description: 'Crisis response guidelines accessed',
    severity: 'medium'
  },
  {
    id: '4',
    timestamp: '09:16:38',
    type: 'draft',
    title: 'Statement Draft Ready',
    description: 'AI-generated response prepared for review',
    severity: 'medium'
  }
];