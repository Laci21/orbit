import React, { useState, useEffect } from 'react';
import { Satellite, Shield } from 'lucide-react';
import { AgentPanel } from './components/AgentPanel';
import { CrisisAlert } from './components/CrisisAlert';
import { SentimentDisplay } from './components/SentimentDisplay';
import { PolicyPanel } from './components/PolicyPanel';
import { StatementDraft } from './components/StatementDraft';
import { Timeline } from './components/Timeline';
import { initialAgents, crisisData, timelineEvents, Agent } from './data/mockData';

function App() {
  const [agents, setAgents] = useState<Agent[]>(initialAgents);
  const [currentStep, setCurrentStep] = useState(-1);
  const [isPublished, setIsPublished] = useState(false);
  const [missionTime, setMissionTime] = useState(0);

  // Auto-progress through the crisis simulation
  useEffect(() => {
    const timer = setInterval(() => {
      setMissionTime(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Trigger crisis detection after 3 seconds
  useEffect(() => {
    if (missionTime === 3 && currentStep === -1) {
      setCurrentStep(0);
      updateAgentStatus('ear-to-ground', 'active', 'Crisis detected! Analyzing viral content...');
    }
  }, [missionTime, currentStep]);

  // Progress through steps automatically
  useEffect(() => {
    if (currentStep >= 0 && currentStep < 4) {
      const timer = setTimeout(() => {
        progressToNextStep();
      }, 4000);

      return () => clearTimeout(timer);
    }
  }, [currentStep]);

  const updateAgentStatus = (agentId: string, status: Agent['status'], action?: string) => {
    setAgents(prev => prev.map(agent => 
      agent.id === agentId 
        ? { ...agent, status, currentAction: action }
        : agent
    ));
  };

  const progressToNextStep = () => {
    const nextStep = currentStep + 1;
    setCurrentStep(nextStep);

    switch (nextStep) {
      case 1:
        updateAgentStatus('ear-to-ground', 'complete');
        updateAgentStatus('sentiment-analyzer', 'active', 'Analyzing public sentiment...');
        break;
      case 2:
        updateAgentStatus('sentiment-analyzer', 'complete');
        updateAgentStatus('fact-checker', 'active', 'Retrieving crisis response protocols...');
        break;
      case 3:
        updateAgentStatus('fact-checker', 'complete');
        updateAgentStatus('press-secretary', 'active', 'Drafting response statement...');
        break;
      case 4:
        updateAgentStatus('press-secretary', 'complete');
        break;
    }
  };

  const handleApprove = () => {
    setIsPublished(true);
    // Reset all agents to idle after publishing
    setTimeout(() => {
      setAgents(prev => prev.map(agent => ({ ...agent, status: 'idle', currentAction: undefined })));
    }, 2000);
  };

  const formatMissionTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-black text-white font-mono">
      {/* Header */}
      <div className="bg-gray-900 border-b border-cyan-500 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Satellite className="w-8 h-8 text-cyan-400" />
              <div>
                <h1 className="text-2xl font-bold text-cyan-400 tracking-wider">THE ORBIT</h1>
                <p className="text-xs text-gray-400">PR Crisis Command Center</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="text-right">
              <div className="text-cyan-400 text-sm font-bold">MISSION TIME</div>
              <div className="text-white text-xl font-mono">{formatMissionTime(missionTime)}</div>
            </div>
            <div className="flex items-center space-x-2">
              {currentStep >= 0 ? (
                <>
                  <div className="w-5 h-5 bg-red-500 rounded-full animate-pulse" />
                  <span className="text-red-400 text-sm font-bold">CRISIS ALERT</span>
                </>
              ) : (
                <>
                  <Shield className="w-5 h-5 text-green-400" />
                  <span className="text-green-400 text-sm">SECURE</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Dashboard */}
      <div className="p-6 grid grid-cols-12 gap-6 h-[calc(100vh-80px)]">
        {/* Left Column - Crisis Alert */}
        <div className="col-span-8">
          <CrisisAlert 
            isActive={currentStep >= 0} 
            tweetData={crisisData.viralTweet}
          />
        </div>

        {/* Right Column - Agent Panel */}
        <div className="col-span-4">
          <AgentPanel agents={agents} />
        </div>

        {/* Second Row - Analysis Panels */}
        <div className="col-span-4">
          <SentimentDisplay 
            isActive={currentStep >= 1} 
            sentimentData={crisisData.sentimentData}
          />
        </div>

        <div className="col-span-4">
          <PolicyPanel 
            isActive={currentStep >= 2} 
            policyData={crisisData.policySnippet}
          />
        </div>

        <div className="col-span-4">
          <StatementDraft 
            isActive={currentStep >= 3}
            isPublished={isPublished}
            draftContent={crisisData.draftStatement}
            onApprove={handleApprove}
          />
        </div>

        {/* Bottom Row - Timeline */}
        <div className="col-span-12">
          <Timeline events={timelineEvents} currentStep={currentStep} />
        </div>
      </div>
    </div>
  );
}

export default App;