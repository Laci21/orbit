import React from 'react';
import { Agent } from '../data/mockData';

interface AgentPanelProps {
  agents: Agent[];
}

export const AgentPanel: React.FC<AgentPanelProps> = ({ agents }) => {
  return (
    <div className="bg-gray-900 border border-cyan-500 rounded-lg p-4 h-full">
      <div className="flex items-center mb-4">
        <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse mr-2"></div>
        <h3 className="text-cyan-400 font-mono text-sm font-bold tracking-wider">
          AGENT STATUS
        </h3>
      </div>
      
      <div className="space-y-3">
        {agents.map((agent) => (
          <div 
            key={agent.id} 
            className={`border rounded p-3 transition-all duration-500 ${
              agent.status === 'active' 
                ? 'border-green-400 bg-green-900/20 shadow-lg shadow-green-400/20' 
                : agent.status === 'complete'
                ? 'border-blue-400 bg-blue-900/20'
                : 'border-gray-600 bg-gray-800/50'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <span className="text-2xl mr-2">{agent.avatar}</span>
                <div>
                  <div className="text-white font-mono text-xs font-bold">
                    {agent.name.toUpperCase()}
                  </div>
                  <div className="text-gray-400 text-xs">
                    {agent.description}
                  </div>
                </div>
              </div>
              <div className={`w-2 h-2 rounded-full ${
                agent.status === 'active' 
                  ? 'bg-green-400 animate-pulse' 
                  : agent.status === 'complete'
                  ? 'bg-blue-400'
                  : 'bg-gray-600'
              }`}></div>
            </div>
            
            {agent.currentAction && agent.status === 'active' && (
              <div className="text-green-300 text-xs font-mono animate-pulse">
                {agent.currentAction}
              </div>
            )}
            
            {agent.status === 'complete' && (
              <div className="text-green-300 text-xs font-mono">
                ✓ Task completed
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};