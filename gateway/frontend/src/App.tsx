import React, { useState, useEffect } from 'react';
import { Satellite, Shield, Play } from 'lucide-react';
import { AgentPanel } from './components/AgentPanel';
import { CrisisAlert } from './components/CrisisAlert';
import { SentimentDisplay } from './components/SentimentDisplay';
import { PolicyPanel } from './components/PolicyPanel';
import { StatementDraft } from './components/StatementDraft';
import { initialAgents, crisisData, Agent } from './data/mockData';
import { useCrisisStatus, triggerCrisis } from './api/orbit';

function App() {
  const [agents, setAgents] = useState<Agent[]>(initialAgents);
  const [isPublished, setIsPublished] = useState(false);
  const [missionTime, setMissionTime] = useState(0);
  const [triggering, setTriggering] = useState(false);

  // Use real API for crisis status
  const { status: crisisStatus, loading, error } = useCrisisStatus();

  // Mission timer
  useEffect(() => {
    const timer = setInterval(() => {
      setMissionTime(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Update agent statuses based on real crisis status
  useEffect(() => {
    if (!crisisStatus) return;

    const progress = crisisStatus.agent_progress || {};
    
    setAgents(prev =>
      prev.map(agent => {
        const agentStatus = progress[agent.id] || 'idle';
        return {
          ...agent,
          status: agentStatus as Agent['status'],
          currentAction: agentStatus === 'active' ? agent.currentAction : undefined
        };
      })
    );
  }, [crisisStatus]);



  const handleTriggerCrisis = async () => {
    if (triggering) return;
    
    setTriggering(true);
    try {
      await triggerCrisis({
        tweet_content: "BREAKING: Major allegations surface against company executive. Investigation needed immediately. #CrisisAlert"
      });
    } catch (err) {
      console.error('Failed to trigger crisis:', err);
    } finally {
      setTriggering(false);
    }
  };

  const handleApprove = () => {
    setIsPublished(true);
    // UI-only approval - no backend call needed per user request
    setTimeout(() => {
      setIsPublished(false);
    }, 3000);
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
            
            {/* Crisis Trigger Button */}
            {(crisisStatus?.status === 'idle' || crisisStatus?.status === 'error' || crisisStatus?.status === 'complete') && (
              <button
                onClick={handleTriggerCrisis}
                disabled={triggering}
                className="flex items-center space-x-2 bg-red-600 hover:bg-red-700 disabled:bg-red-800 px-4 py-2 rounded font-bold text-sm"
              >
                <Play className="w-4 h-4" />
                <span>{triggering ? 'TRIGGERING...' : (crisisStatus?.status === 'complete' ? 'RETRIGGER CRISIS' : 'TRIGGER CRISIS')}</span>
              </button>
            )}
            
            <div className="flex items-center space-x-2">
              {crisisStatus?.status === 'active' ? (
                <>
                  <div className="w-5 h-5 bg-red-500 rounded-full animate-pulse" />
                  <span className="text-red-400 text-sm font-bold">CRISIS ACTIVE</span>
                </>
              ) : crisisStatus?.status === 'complete' ? (
                <>
                  <div className="w-5 h-5 bg-yellow-500 rounded-full" />
                  <span className="text-yellow-400 text-sm font-bold">RESPONSE READY</span>
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
      <div className="p-8 grid grid-cols-12 gap-8 h-[calc(100vh-80px)]">
        {/* Left Column - Crisis Alert */}
        <div className="col-span-8">
          <CrisisAlert 
            isActive={crisisStatus?.status === 'active' || crisisStatus?.status === 'complete'} 
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
            isActive={crisisStatus?.status === 'active' || crisisStatus?.status === 'complete'} 
            sentimentData={crisisData.sentimentData}
            liveData={crisisStatus?.agent_results?.sentiment_analyst}
          />
        </div>

        <div className="col-span-4">
          <PolicyPanel 
            isActive={crisisStatus?.status === 'active' || crisisStatus?.status === 'complete'} 
            policyData={crisisData.policySnippet}
            factData={crisisStatus?.agent_results?.fact_checker}
            legalData={crisisStatus?.agent_results?.legal_counsel}
            riskData={crisisStatus?.agent_results?.risk_score}
          />
        </div>

        <div className="col-span-4">
          <StatementDraft 
            isActive={!!crisisStatus?.agent_results?.press_secretary || crisisStatus?.status === 'complete'}
            isPublished={isPublished}
            draftContent={crisisStatus?.final_response ? "AI-generated response ready for review" : crisisData.draftStatement}
            finalResponse={crisisStatus?.final_response || (crisisStatus?.agent_results?.press_secretary ? { press_secretary_response: crisisStatus.agent_results.press_secretary } : undefined)}
            onApprove={handleApprove}
          />
        </div>


      </div>
    </div>
  );
}

export default App;