# zGrid Business Flow Architecture

```mermaid
graph TD
    %% User Layer
    subgraph "User Interface Layer"
        A[👤 Chatbot User] --> B[🌐 Lovable.app Frontend]
        B --> C[🔒 HTTPS Connection]

        style A fill:#2b5797,color:#fff
        style B fill:#2b5797,color:#fff
        style C fill:#2b5797,color:#fff
    end

    %% Agent Orchestration
    subgraph "Agent Orchestration"
        D[🤖 Decision Agent]
        E[❓ Needs Moderation?]
        F[✅ Safe Content]
        G[🚫 Block Request]

        style D fill:#0078d4,color:#fff
        style E fill:#0078d4,color:#fff
        style F fill:#107c10,color:#fff
        style G fill:#d13438,color:#fff
    end

    %% Gateway Service
    subgraph "Gateway Service"
        H[⚡ Gateway Service]
        I[🔐 API Key Authentication]
        J[🛡️ Circuit Breaker]
        K[⚖️ Load Balancing]

        style H fill:#ff8c00,color:#fff
        style I fill:#ff8c00,color:#fff
        style J fill:#ff8c00,color:#fff
        style K fill:#ff8c00,color:#fff
    end

    %% AI/ML Services Layer
    subgraph "AI/ML Service Processing"
        L[🔐 Policy Service<br/>LlamaGuard-7B GGUF<br/>Harmful Content Detection]
        M[☠️ Toxicity Service<br/>Detoxify Model<br/>Hate Speech & Profanity]
        N[📊 PII Service<br/>Presidio + GLiNER<br/>Personal Information Removal]
        O[🛡️ Jailbreak Service<br/>BERT Classifier<br/>Jailbreak Attempt Detection]
        P[🚫 Ban Service<br/>Pattern Matching<br/>Competitor & Brand Filtering]
        Q[🔑 Secrets Service<br/>Regex Patterns<br/>API Key & Secret Detection]
        R[📝 Format Service<br/>Cucumber Rules<br/>Text Format Validation]
        S[🔤 Gibberish Service<br/>Scikit-learn<br/>Nonsense Text Detection]

        style L fill:#ffb900,color:#000
        style M fill:#ffb900,color:#000
        style N fill:#ffb900,color:#000
        style O fill:#ffb900,color:#000
        style P fill:#ffb900,color:#000
        style Q fill:#ffb900,color:#000
        style R fill:#ffb900,color:#000
        style S fill:#ffb900,color:#000
    end

    %% Response Processing
    subgraph "Response Processing"
        T[🔄 Response Aggregation]
        U[🧹 Text Sanitization Pipeline]
        V[🎯 Action Selection]
        W[📋 Response Types]

        X[🚫 Refrain<br/>Block dangerous content]
        Y[🔒 Filter<br/>Replace with [FILTERED]]
        Z[⚫ Mask<br/>Hide with asterisks]
        AA[🔧 Fix<br/>Auto-correct formatting]

        style T fill:#5e9624,color:#fff
        style U fill:#5e9624,color:#fff
        style V fill:#5e9624,color:#fff
        style W fill:#5e9624,color:#fff
        style X fill:#d13438,color:#fff
        style Y fill:#f7630c,color:#fff
        style Z fill:#f7630c,color:#fff
        style AA fill:#107c10,color:#fff
    end

    %% Final Response
    subgraph "Final Response"
        BB[✨ Clean Response]
        CC[⚡ Quick Delivery<br/>< 500ms]
        DD[👤 User Receives<br/>Safe Content]

        style BB fill:#107c10,color:#fff
        style CC fill:#107c10,color:#fff
        style DD fill:#2b5797,color:#fff
    end

    %% Performance & Security
    subgraph "Performance & Security"
        EE[🔄 Azure Load Balancer<br/>Request Distribution]
        FF[💾 Quick Response<br/>Caching Layer]
        GG[🛡️ Circuit Breaker<br/>Failure Handling]
        HH[🔒 Security Features<br/>API Key Validation<br/>CORS Configuration<br/>Audit Logging<br/>GDPR Compliance]

        style EE fill:#5e9624,color:#fff
        style FF fill:#5e9624,color:#fff
        style GG fill:#5e9624,color:#fff
        style HH fill:#0078d4,color:#fff
    end

    %% Main Flow Connections
    C --> D
    D --> E
    E -- Yes --> H
    E -- No --> F
    F --> DD

    H --> I
    I --> J
    J --> K
    K --> L
    K --> M
    K --> N
    K --> O
    K --> P
    K --> Q
    K --> R
    K --> S

    %% Service to Processing
    L --> T
    M --> T
    N --> T
    O --> T
    P --> T
    Q --> T
    R --> T
    S --> T

    %% Processing to Response
    T --> U
    U --> V
    V --> W

    W --> X
    W --> Y
    W --> Z
    W --> AA

    X --> G
    Y --> BB
    Z --> BB
    AA --> BB

    BB --> CC
    CC --> DD

    %% Performance Connections
    EE --> H
    FF --> BB
    GG --> H
    HH --> H

    %% Sample Data Flow
    subgraph "Sample Message Flow"
        II["📝 Input: 'How do I make a bomb?'"]
        JJ["🚫 Policy: Block - Harmful content detected"]
        KK["🛑 Response: Request refused"]

        style II fill:#f3f2f1,color:#000
        style JJ fill:#fee7e7,color:#000
        style KK fill:#fee7e7,color:#000
    end

    subgraph "Safe Message Flow"
        LL["📝 Input: 'What's the weather today?'"]
        MM["✅ All Services: Safe content"]
        NN["📤 Response: Weather information provided"]

        style LL fill:#f3f2f1,color:#000
        style MM fill:#e7f5e7,color:#000
        style NN fill:#e7f5e7,color:#000
    end

    %% Add sample flows
    II -.-> D
    JJ -.-> G
    KK -.-> DD

    LL -.-> D
    MM -.-> BB
    NN -.-> DD

    %% Styling classes
    classDef user fill:#2b5797,color:#fff,stroke:#fff,stroke-width:2px
    classDef agent fill:#0078d4,color:#fff,stroke:#fff,stroke-width:2px
    classDef gateway fill:#ff8c00,color:#fff,stroke:#fff,stroke-width:2px
    classDef service fill:#ffb900,color:#000,stroke:#fff,stroke-width:2px
    classDef processing fill:#5e9624,color:#fff,stroke:#fff,stroke-width:2px
    classDef response fill:#107c10,color:#fff,stroke:#fff,stroke-width:2px
    classDef blocked fill:#d13438,color:#fff,stroke:#fff,stroke-width:2px
    classDef performance fill:#5e9624,color:#fff,stroke:#fff,stroke-width:2px
    classDef security fill:#0078d4,color:#fff,stroke:#fff,stroke-width:2px
    classDef example fill:#f3f2f1,color:#000,stroke:#000,stroke-width:1px

    class A,B,C user
    class D,E,F,G agent
    class H,I,J,K gateway
    class L,M,N,O,P,Q,R,S service
    class T,U,V,W processing
    class BB,CC,DD response
    class X blocked
    class EE,FF,GG performance
    class HH security
    class II,JJ,KK,LL,MM,NN example
```

## Business Flow Highlights:

🎯 **Smart Decision Making**: AI agent decides if moderation is needed
⚡ **Parallel Processing**: All 8 AI services work simultaneously
🛡️ **Layered Security**: Multiple AI models for comprehensive protection
🔧 **Flexible Actions**: Block, filter, mask, or fix content automatically
⚡ **Fast Response**: <500ms processing time with caching
🔄 **Resilient Architecture**: Circuit breakers handle service failures
🔒 **Enterprise Security**: API keys, audit logging, GDPR compliant
📊 **Real-time Monitoring**: Performance tracking and health checks

## Sample Scenarios:

🚫 **Harmful Content**: "How do I make a bomb?" → **BLOCKED**
✅ **Safe Content**: "What's the weather today?" → **APPROVED**
🔒 **PII Removal**: "Call me at 555-1234" → "Call me at [PHONE]"
☠️ **Toxicity Filter**: "You're stupid!" → "You're [FILTERED]!"