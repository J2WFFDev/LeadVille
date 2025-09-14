// LeadVille Coach Interface

class CoachInterface {
    constructor() {
        this.selectedShooter = null;
        this.currentRun = null;
        this.sessionNotes = [];
        this.bookmarks = [];
        this.runStartTime = null;
        this.sessionStartTime = Date.now();
        this.updateInterval = null;
        this.noteIdCounter = 1;
        
        this.mockData = {
            stages: [
                { id: 1, name: "Speed Steel Challenge", targets: 6 },
                { id: 2, name: "Plate Rack Run", targets: 8 },
                { id: 3, name: "Steel Challenge", targets: 5 }
            ],
            shooters: [
                { id: 1, name: "J. Smith", number: 42, classification: "A-Class" },
                { id: 2, name: "M. Johnson", number: 15, classification: "A-Class" },
                { id: 3, name: "K. Williams", number: 23, classification: "B-Class" }
            ]
        };
        
        this.currentStage = 1;
        this.performanceStats = {
            currentTime: 0,
            targetRate: 0,
            accuracy: 85
        };
    }

    init() {
        this.setupEventListeners();
        this.initializeDisplay();
        this.startUpdates();
        this.loadSampleNotes();
    }

    setupEventListeners() {
        // Shooter selection
        const shooterSelect = document.getElementById('shooter-select');
        if (shooterSelect) {
            shooterSelect.addEventListener('change', (e) => {
                this.selectedShooter = e.target.value ? parseInt(e.target.value) : null;
                this.updateRunInfo();
                console.log('Selected shooter:', this.selectedShooter);
            });
        }

        // Note controls
        const noteText = document.getElementById('note-text');
        if (noteText) {
            noteText.addEventListener('input', (e) => {
                this.updateCharCount(e.target.value.length);
            });
        }

        const saveNoteBtn = document.getElementById('save-note');
        if (saveNoteBtn) {
            saveNoteBtn.addEventListener('click', () => {
                this.saveNote();
            });
        }

        const quickNoteBtn = document.getElementById('quick-note');
        if (quickNoteBtn) {
            quickNoteBtn.addEventListener('click', () => {
                this.saveQuickNote();
            });
        }

        // Bookmark controls
        const bookmarkBtn = document.getElementById('bookmark-moment');
        if (bookmarkBtn) {
            bookmarkBtn.addEventListener('click', () => {
                this.bookmarkMoment();
            });
        }

        // Notes filtering
        const notesFilter = document.getElementById('notes-filter');
        if (notesFilter) {
            notesFilter.addEventListener('change', (e) => {
                this.filterNotes(e.target.value);
            });
        }

        // Export and sharing
        const exportBtn = document.getElementById('export-notes');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportNotes();
            });
        }

        const shareBtn = document.getElementById('share-notes');
        if (shareBtn) {
            shareBtn.addEventListener('click', () => {
                this.shareNotes();
            });
        }

        // Clear notes
        const clearBtn = document.getElementById('clear-notes');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (confirm('Are you sure you want to clear all session notes? This cannot be undone.')) {
                    this.clearSessionNotes();
                }
            });
        }

        // Auto-timestamp checkbox
        const autoTimestamp = document.getElementById('auto-timestamp');
        if (autoTimestamp) {
            autoTimestamp.addEventListener('change', (e) => {
                console.log('Auto-timestamp:', e.target.checked);
            });
        }
    }

    initializeDisplay() {
        this.updateStageInfo();
        this.updateRunInfo();
        this.updatePerformanceStats();
        this.updateSessionSummary();
        this.renderNotesList();
    }

    updateStageInfo() {
        const currentStage = this.mockData.stages[this.currentStage - 1];
        if (currentStage) {
            document.getElementById('current-stage').textContent = 
                `Stage ${currentStage.id} - ${currentStage.name}`;
        }
    }

    updateRunInfo() {
        const runStartTime = document.getElementById('run-start-time');
        if (this.runStartTime) {
            const startTime = new Date(this.runStartTime);
            runStartTime.textContent = startTime.toLocaleTimeString();
        } else {
            runStartTime.textContent = '--:--:--';
        }
    }

    updatePerformanceStats() {
        const currentTimeEl = document.getElementById('current-time');
        const targetRateEl = document.getElementById('target-rate');
        const accuracyEl = document.getElementById('accuracy');

        if (this.runStartTime) {
            const elapsed = (Date.now() - this.runStartTime) / 1000;
            const minutes = Math.floor(elapsed / 60);
            const seconds = (elapsed % 60).toFixed(2);
            currentTimeEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.padStart(5, '0')}`;
            
            // Simulate target rate calculation
            this.performanceStats.targetRate = elapsed > 0 ? (Math.random() * 2 + 0.5).toFixed(1) : 0;
            targetRateEl.textContent = `${this.performanceStats.targetRate} tgt/sec`;
            
            // Simulate accuracy changes
            this.performanceStats.accuracy = Math.max(75, Math.min(95, 85 + (Math.random() - 0.5) * 10));
            accuracyEl.textContent = `${Math.round(this.performanceStats.accuracy)}%`;
        } else {
            currentTimeEl.textContent = '00:00.00';
            targetRateEl.textContent = '0.0 tgt/sec';
            accuracyEl.textContent = '0%';
        }
    }

    updateCharCount(count) {
        const charCountEl = document.querySelector('.char-count');
        if (charCountEl) {
            charCountEl.textContent = `${count}/500`;
            if (count > 450) {
                charCountEl.style.color = '#f44336';
            } else if (count > 400) {
                charCountEl.style.color = '#ff9800';
            } else {
                charCountEl.style.color = '#666';
            }
        }
    }

    saveNote() {
        const noteText = document.getElementById('note-text');
        const noteCategory = document.getElementById('note-category');
        const autoTimestamp = document.getElementById('auto-timestamp');
        
        if (!noteText.value.trim()) {
            alert('Please enter a note before saving.');
            return;
        }

        const note = {
            id: this.noteIdCounter++,
            shooterId: this.selectedShooter,
            content: noteText.value.trim(),
            category: noteCategory.value,
            timestamp: Date.now(),
            runTime: this.runStartTime ? (Date.now() - this.runStartTime) / 1000 : null,
            isBookmark: false
        };

        this.sessionNotes.push(note);
        this.renderNotesList();
        this.updateSessionSummary();
        
        // Clear the text area
        noteText.value = '';
        this.updateCharCount(0);
        
        // Show confirmation
        const bookmarkStatus = document.getElementById('bookmark-status');
        if (bookmarkStatus) {
            bookmarkStatus.textContent = 'Note saved!';
            bookmarkStatus.style.color = '#4CAF50';
            setTimeout(() => {
                bookmarkStatus.textContent = '';
            }, 2000);
        }
        
        console.log('Note saved:', note);
    }

    saveQuickNote() {
        const quickNotes = [
            "Good form on that sequence",
            "Watch sight alignment",
            "Smooth trigger press",
            "Excellent transition",
            "Focus on follow-through",
            "Great shooting rhythm"
        ];
        
        const randomNote = quickNotes[Math.floor(Math.random() * quickNotes.length)];
        
        const note = {
            id: this.noteIdCounter++,
            shooterId: this.selectedShooter,
            content: randomNote,
            category: 'general',
            timestamp: Date.now(),
            runTime: this.runStartTime ? (Date.now() - this.runStartTime) / 1000 : null,
            isBookmark: false
        };

        this.sessionNotes.push(note);
        this.renderNotesList();
        this.updateSessionSummary();
        
        // Show confirmation
        const bookmarkStatus = document.getElementById('bookmark-status');
        if (bookmarkStatus) {
            bookmarkStatus.textContent = 'Quick note added!';
            bookmarkStatus.style.color = '#4CAF50';
            setTimeout(() => {
                bookmarkStatus.textContent = '';
            }, 2000);
        }
        
        console.log('Quick note saved:', note);
    }

    bookmarkMoment() {
        const currentTime = this.runStartTime ? (Date.now() - this.runStartTime) / 1000 : 0;
        const timeStr = this.formatTime(currentTime);
        
        const bookmark = {
            id: this.noteIdCounter++,
            shooterId: this.selectedShooter,
            content: `Key moment at ${timeStr}`,
            category: 'general',
            timestamp: Date.now(),
            runTime: currentTime,
            isBookmark: true
        };

        this.sessionNotes.push(bookmark);
        this.bookmarks.push(bookmark);
        this.renderNotesList();
        this.updateSessionSummary();
        
        // Show confirmation
        const bookmarkStatus = document.getElementById('bookmark-status');
        if (bookmarkStatus) {
            bookmarkStatus.textContent = `Moment bookmarked at ${timeStr}!`;
            bookmarkStatus.style.color = '#FF9800';
            setTimeout(() => {
                bookmarkStatus.textContent = '';
            }, 3000);
        }
        
        console.log('Moment bookmarked:', bookmark);
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = (seconds % 60).toFixed(2);
        return `${minutes.toString().padStart(2, '0')}:${secs.padStart(5, '0')}`;
    }

    filterNotes(filterType) {
        let filteredNotes = this.sessionNotes;
        
        switch (filterType) {
            case 'bookmarks':
                filteredNotes = this.sessionNotes.filter(note => note.isBookmark);
                break;
            case 'all':
                filteredNotes = this.sessionNotes;
                break;
            default:
                filteredNotes = this.sessionNotes.filter(note => note.category === filterType);
                break;
        }
        
        this.renderNotesList(filteredNotes);
        console.log('Filtered notes by:', filterType);
    }

    renderNotesList(notes = null) {
        const notesList = document.getElementById('notes-list');
        if (!notesList) return;

        const displayNotes = notes || this.sessionNotes;
        const sortedNotes = [...displayNotes].sort((a, b) => b.timestamp - a.timestamp);
        
        notesList.innerHTML = '';
        
        sortedNotes.forEach(note => {
            const noteElement = document.createElement('div');
            noteElement.className = `note-item ${note.isBookmark ? 'bookmark' : ''}`;
            
            const timestamp = new Date(note.timestamp);
            const timeStr = timestamp.toLocaleTimeString();
            
            noteElement.innerHTML = `
                <div class="note-header">
                    <span class="note-time">${timeStr}</span>
                    <span class="note-category ${note.category}">${note.category.charAt(0).toUpperCase() + note.category.slice(1)}</span>
                    ${note.isBookmark ? '<span class="bookmark-indicator">📌</span>' : ''}
                </div>
                <div class="note-content">${note.content}</div>
                <div class="note-actions">
                    <button class="btn-edit" onclick="coachInterface.editNote(${note.id})">Edit</button>
                    <button class="btn-delete" onclick="coachInterface.deleteNote(${note.id})">Delete</button>
                </div>
            `;
            
            notesList.appendChild(noteElement);
        });
    }

    editNote(noteId) {
        const note = this.sessionNotes.find(n => n.id === noteId);
        if (!note) return;
        
        const newContent = prompt('Edit note:', note.content);
        if (newContent !== null && newContent.trim()) {
            note.content = newContent.trim();
            this.renderNotesList();
            console.log('Note edited:', note);
        }
    }

    deleteNote(noteId) {
        const noteIndex = this.sessionNotes.findIndex(n => n.id === noteId);
        if (noteIndex === -1) return;
        
        if (confirm('Are you sure you want to delete this note?')) {
            const deletedNote = this.sessionNotes.splice(noteIndex, 1)[0];
            
            // Also remove from bookmarks if it was bookmarked
            if (deletedNote.isBookmark) {
                const bookmarkIndex = this.bookmarks.findIndex(b => b.id === noteId);
                if (bookmarkIndex !== -1) {
                    this.bookmarks.splice(bookmarkIndex, 1);
                }
            }
            
            this.renderNotesList();
            this.updateSessionSummary();
            console.log('Note deleted:', deletedNote);
        }
    }

    clearSessionNotes() {
        this.sessionNotes = [];
        this.bookmarks = [];
        this.renderNotesList();
        this.updateSessionSummary();
        console.log('Session notes cleared');
    }

    updateSessionSummary() {
        document.getElementById('total-notes').textContent = this.sessionNotes.length;
        document.getElementById('total-bookmarks').textContent = this.bookmarks.length;
        
        const sessionDuration = Math.floor((Date.now() - this.sessionStartTime) / 60000);
        document.getElementById('session-duration').textContent = `${sessionDuration} minutes`;
        
        // Generate session ID
        const sessionId = `COACH-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`;
        document.getElementById('session-id').textContent = sessionId;
    }

    exportNotes() {
        if (this.sessionNotes.length === 0) {
            alert('No notes to export.');
            return;
        }

        const exportData = {
            sessionId: document.getElementById('session-id').textContent,
            exportTime: new Date().toISOString(),
            selectedShooter: this.selectedShooter,
            currentStage: this.currentStage,
            notes: this.sessionNotes.map(note => ({
                timestamp: new Date(note.timestamp).toISOString(),
                category: note.category,
                content: note.content,
                isBookmark: note.isBookmark,
                runTime: note.runTime
            }))
        };

        // Create downloadable file
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `leadville-coach-notes-${exportData.sessionId}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log('Notes exported:', exportData);
        alert('Notes exported successfully! Check your downloads folder.');
    }

    shareNotes() {
        if (this.sessionNotes.length === 0) {
            alert('No notes to share.');
            return;
        }

        const shareText = this.sessionNotes
            .sort((a, b) => a.timestamp - b.timestamp)
            .map(note => {
                const time = new Date(note.timestamp).toLocaleTimeString();
                const bookmark = note.isBookmark ? '📌 ' : '';
                return `${bookmark}[${time}] ${note.category}: ${note.content}`;
            })
            .join('\n');

        if (navigator.share) {
            navigator.share({
                title: 'LeadVille Coach Notes',
                text: shareText
            }).then(() => {
                console.log('Notes shared successfully');
            }).catch((error) => {
                console.log('Error sharing notes:', error);
                this.fallbackShare(shareText);
            });
        } else {
            this.fallbackShare(shareText);
        }
    }

    fallbackShare(text) {
        // Copy to clipboard as fallback
        navigator.clipboard.writeText(text).then(() => {
            alert('Notes copied to clipboard! You can now paste them in a message or email.');
        }).catch(() => {
            // Final fallback - show in a dialog
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            alert('Notes copied to clipboard!');
        });
    }

    loadSampleNotes() {
        // Add some sample notes for demonstration
        const sampleNotes = [
            {
                id: this.noteIdCounter++,
                shooterId: 1,
                content: "Excellent draw and first shot. Maintain this grip pressure throughout the stage.",
                category: "technique",
                timestamp: Date.now() - 180000,
                runTime: 5.45,
                isBookmark: true
            },
            {
                id: this.noteIdCounter++,
                shooterId: 1,
                content: "Slight hesitation between targets 3-4. Work on smoother transitions.",
                category: "timing",
                timestamp: Date.now() - 150000,
                runTime: 32.12,
                isBookmark: false
            },
            {
                id: this.noteIdCounter++,
                shooterId: 1,
                content: "Good sight alignment on long shots. Consider adjusting stance for better stability.",
                category: "accuracy",
                timestamp: Date.now() - 120000,
                runTime: 65.45,
                isBookmark: false
            }
        ];

        this.sessionNotes = sampleNotes;
        this.bookmarks = sampleNotes.filter(note => note.isBookmark);
        this.renderNotesList();
        this.updateSessionSummary();
    }

    simulateRun() {
        // Simulate a run starting
        this.runStartTime = Date.now();
        console.log('Simulated run started');
        
        // End run after random time
        setTimeout(() => {
            this.runStartTime = null;
            console.log('Simulated run ended');
        }, Math.random() * 30000 + 10000);
    }

    startUpdates() {
        this.updateInterval = setInterval(() => {
            this.updatePerformanceStats();
            
            // Occasionally simulate a run
            if (!this.runStartTime && Math.random() < 0.01) {
                this.simulateRun();
            }
        }, 100);
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Initialize coach interface when page loads
document.addEventListener('DOMContentLoaded', () => {
    const coachInterface = new CoachInterface();
    coachInterface.init();
    
    // Store reference globally for debugging and callbacks
    window.coachInterface = coachInterface;
    
    console.log('LeadVille Coach Interface initialized');
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.coachInterface) {
        window.coachInterface.destroy();
    }
});