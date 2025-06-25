document.addEventListener("DOMContentLoaded", () => {
    // --- Element Selectors ---
    const views = document.querySelectorAll(".view"); // A class for all top-level views
    const authView = document.getElementById("auth-view");
    const appView = document.getElementById("app-view");
    const groupDetailView = document.getElementById("group-detail-view");
    
    const loader = document.getElementById("loader");
    const toast = document.getElementById("toast-notification");

    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const logoutButton = document.getElementById("logout-button");

    const userEmailSpan = document.getElementById("user-email");
    const groupsListDiv = document.getElementById("groups-list");
    
    const tabs = document.querySelectorAll(".tab-link");
    const tabContents = document.querySelectorAll(".tab-content");

    // --- State Management ---
    let currentGroupId = null; // To keep track of the currently viewed group

    // --- Utility Functions ---
    const showLoader = () => loader.classList.remove("hidden");
    const hideLoader = () => loader.classList.add("hidden");

    const showToast = (message, type = 'success') => {
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        setTimeout(() => { toast.className = 'toast'; }, 3000);
    };

    const getToken = () => localStorage.getItem("access_token");

    // NEW: Generic function to switch between views
    const showView = (viewId) => {
        document.querySelectorAll('#auth-view, #app-view, #group-detail-view').forEach(view => {
            view.classList.add('hidden');
        });
        document.getElementById(viewId).classList.remove('hidden');
    };

    const updateUIForLoginState = () => {
        const token = getToken();
        if (token) {
            showView('app-view'); // Default to the groups list view
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                userEmailSpan.textContent = payload.sub;
                fetchGroups();
            } catch (e) {
                localStorage.removeItem("access_token");
                updateUIForLoginState(); // Re-run to show auth view
            }
        } else {
            showView('auth-view');
        }
    };
    
    // --- API Call Functions ---
    const fetchGroups = async () => {
        const token = getToken();
        if (!token) return;

        showLoader();
        try {
            const response = await fetch("/groups", {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error("Could not fetch groups.");

            const groups = await response.json();
            groupsListDiv.innerHTML = "";
            if (groups.length === 0) {
                groupsListDiv.innerHTML = "<div class='card' style='text-align:center;'><p>You haven't created any groups yet.</p></div>";
            } else {
                groups.forEach(group => {
                    const groupEl = document.createElement("div");
                    groupEl.className = "group-item";
                    groupEl.dataset.groupId = group.group_id; // IMPORTANT: Add group ID for click handling
                    groupEl.innerHTML = `
                        <h3>${group.name}</h3>
                        <p><i class="fas fa-users"></i><strong>Members:</strong> ${Array.from(group.members).join(", ")}</p>
                    `;
                    groupsListDiv.appendChild(groupEl);
                });
            }
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            hideLoader();
        }
    };

    // NEW: Function to fetch and display details for a single group
    const showGroupDetail = async (groupId) => {
        currentGroupId = groupId;
        showView('group-detail-view');
        showLoader();

        try {
            const token = getToken();
            // NOTE: This endpoint doesn't exist yet! We will build it next.
            const response = await fetch(`/groups/${groupId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!response.ok) throw new Error("Could not load group details.");
            
            const group = await response.json();

            // Populate the header and form
            document.getElementById('group-detail-title').textContent = group.name;
            populateExpenseForm(group.members);
            
            // NOTE: This endpoint also doesn't exist yet!
            const expensesResponse = await fetch(`/groups/${groupId}/expenses`, {
                 headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!expensesResponse.ok) throw new Error("Could not load expenses.");
            const expenses = await expensesResponse.json();
            renderExpenses(expenses);

        } catch (error) {
            showToast(error.message, "error");
            showView('app-view'); // Go back if there's an error
        } finally {
            hideLoader();
        }
    };
    
    // NEW: Function to populate the expense form with group members
    const populateExpenseForm = (members) => {
        const payerSelect = document.getElementById('expense-payer');
        const participantsList = document.getElementById('expense-participants-list');

        payerSelect.innerHTML = '<option value="" disabled selected>Who paid?</option>';
        participantsList.innerHTML = '';

        members.forEach(member => {
            // Populate payer dropdown
            const option = document.createElement('option');
            option.value = member;
            option.textContent = member;
            payerSelect.appendChild(option);

            // Populate participants checkboxes
            const checkboxItem = document.createElement('div');
            checkboxItem.className = 'checkbox-item';
            checkboxItem.innerHTML = `
                <input type="checkbox" id="participant-${member}" name="participants" value="${member}" checked>
                <label for="participant-${member}">${member}</label>
            `;
            participantsList.appendChild(checkboxItem);
        });
    };
    
    // NEW: Function to render the list of expenses for a group
    const renderExpenses = (expenses) => {
        const expensesListDiv = document.getElementById('expenses-list');
        expensesListDiv.innerHTML = '';
        if (expenses.length === 0) {
            expensesListDiv.innerHTML = "<p style='text-align:center;'>No expenses added yet. Be the first!</p>";
            return;
        }

        expenses.forEach(expense => {
            const expenseEl = document.createElement('div');
            expenseEl.className = 'expense-item';
            expenseEl.innerHTML = `
                <p class="description">${expense.description}</p>
                <div class="expense-details">
                    <span class="payer">Paid by <strong>${expense.payer}</strong></span>
                    <span class="amount">₹${expense.amount.toFixed(2)}</span>
                </div>
                <div class="expense-participants">
                    Split between: ${expense.participants.join(', ')}
                </div>
            `;
            expensesListDiv.appendChild(expenseEl);
        });
    };

    // --- Event Listeners ---
    
    // Login, Register, Tabs, Logout (Unchanged from previous version)
    tabs.forEach(tab => { tab.addEventListener("click", () => { tabs.forEach(t => t.classList.remove("active")); tabContents.forEach(c => c.classList.remove("active")); tab.classList.add("active"); document.getElementById(tab.dataset.tab).classList.add("active"); }); });
    const handleAuthFormSubmit = async (url, formData, successMessage, formToReset) => { showLoader(); try { const response = await fetch(url, { method: "POST", body: formData }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "An error occurred."); showToast(successMessage, "success"); if (formToReset) formToReset.reset(); return data; } catch (error) { showToast(error.message, "error"); } finally { hideLoader(); } };
    registerForm.addEventListener("submit", async (e) => { e.preventDefault(); const formData = new FormData(); formData.append('username', document.getElementById('register-email').value); formData.append('password', document.getElementById('register-password').value); await handleAuthFormSubmit("/register", formData, "Registration successful! Please log in.", registerForm); });
    loginForm.addEventListener("submit", async (e) => { e.preventDefault(); const formData = new FormData(); formData.append('username', document.getElementById('login-email').value); formData.append('password', document.getElementById('login-password').value); const data = await handleAuthFormSubmit("/token", formData, "Login successful!", loginForm); if (data && data.access_token) { localStorage.setItem("access_token", data.access_token); updateUIForLoginState(); } });
    logoutButton.addEventListener("click", () => { localStorage.removeItem("access_token"); showToast("Logged out successfully.", "success"); updateUIForLoginState(); });
    
    // Group Creation Logic (Unchanged from previous version)
    const createGroupForm = document.getElementById("create-group-form"); const memberNameInput = document.getElementById("member-name-input"); const addMemberButton = document.getElementById("add-member-button"); const membersListContainer = document.getElementById("members-list-container"); const createGroupButton = document.getElementById("create-group-button"); let currentMembers = []; const renderMembersList = () => { membersListContainer.innerHTML = ""; currentMembers.forEach(member => { const pill = document.createElement("div"); pill.className = "member-pill"; const safeMemberName = member.replace(/</g, "<").replace(/>/g, ">"); pill.innerHTML = `<span>${safeMemberName}</span><button type="button" class="remove-member-btn" data-member="${safeMemberName}">×</button>`; membersListContainer.appendChild(pill); }); validateCreateGroupButton(); }; const validateCreateGroupButton = () => { createGroupButton.disabled = currentMembers.length < 1; }; const addMember = () => { const newMemberName = memberNameInput.value.trim(); if (!newMemberName) { showToast("Member name cannot be empty.", "error"); return; } if (currentMembers.map(m => m.toLowerCase()).includes(newMemberName.toLowerCase())) { showToast("This member has already been added.", "error"); return; } currentMembers.push(newMemberName); renderMembersList(); memberNameInput.value = ""; memberNameInput.focus(); }; addMemberButton.addEventListener("click", addMember); memberNameInput.addEventListener("keydown", (e) => { if (e.key === 'Enter') { e.preventDefault(); addMember(); } }); membersListContainer.addEventListener("click", (e) => { if (e.target && e.target.classList.contains("remove-member-btn")) { const memberToRemove = e.target.dataset.member; currentMembers = currentMembers.filter(m => m !== memberToRemove); renderMembersList(); } });
    createGroupForm.addEventListener("submit", async (e) => { e.preventDefault(); if (currentMembers.length < 1) { showToast("You must add at least one member to the group.", "error"); return; } showLoader(); try { const token = getToken(); const groupName = document.getElementById("group-name").value; const members = currentMembers; const response = await fetch("/groups", { method: "POST", headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }, body: JSON.stringify({ name: groupName, members: members }) }); const data = await response.json(); if (!response.ok) throw new Error(data.detail || "Failed to create group."); showToast("Group created successfully!", "success"); document.getElementById("group-name").value = ""; currentMembers = []; renderMembersList(); fetchGroups(); } catch (error) { showToast(error.message, "error"); } finally { hideLoader(); } });

    // --- NEW Event Listeners for Group Details ---
    
    // Use event delegation to handle clicks on dynamically created group items
    groupsListDiv.addEventListener("click", (e) => {
        const groupItem = e.target.closest(".group-item");
        if (groupItem) {
            const groupId = groupItem.dataset.groupId;
            showGroupDetail(groupId);
        }
    });

    document.getElementById('back-to-groups-button').addEventListener('click', () => {
        currentGroupId = null;
        showView('app-view');
        fetchGroups(); // Refresh group list in case of any updates
    });
    
    document.getElementById('add-expense-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!currentGroupId) return;

        const description = document.getElementById('expense-description').value;
        const amount = parseFloat(document.getElementById('expense-amount').value);
        const payer = document.getElementById('expense-payer').value;
        const participants = Array.from(document.querySelectorAll('#expense-participants-list input:checked')).map(el => el.value);

        if (!description || !amount || !payer || participants.length === 0) {
            showToast("Please fill out all expense fields.", "error");
            return;
        }

        showLoader();
        try {
            const token = getToken();
            // NOTE: This endpoint doesn't exist yet! We will build it next.
            const response = await fetch(`/groups/${currentGroupId}/expenses`, {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ description, amount, payer, participants })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to add expense.");
            }
            
            showToast("Expense added successfully!", "success");
            e.target.reset(); // Reset the form
            showGroupDetail(currentGroupId); // Refresh the view

        } catch (error) {
            showToast(error.message, "error");
        } finally {
            hideLoader();
        }
    });

    // --- Initial Load ---
    updateUIForLoginState();
});