document.addEventListener("DOMContentLoaded", () => {
    // --- Element Selectors ---
    const authView = document.getElementById("auth-view");
    const appView = document.getElementById("app-view");
    const loader = document.getElementById("loader");
    const toast = document.getElementById("toast-notification");

    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const logoutButton = document.getElementById("logout-button");

    const userEmailSpan = document.getElementById("user-email");
    const groupsListDiv = document.getElementById("groups-list");
    
    const tabs = document.querySelectorAll(".tab-link");
    const tabContents = document.querySelectorAll(".tab-content");

    // --- Utility Functions ---
    const showLoader = () => loader.classList.remove("hidden");
    const hideLoader = () => loader.classList.add("hidden");

    const showToast = (message, type = 'success') => {
        toast.textContent = message;
        toast.className = `toast show ${type}`;
        setTimeout(() => {
            toast.className = 'toast';
        }, 3000);
    };

    const getToken = () => localStorage.getItem("access_token");

    const updateUI = () => {
        const token = getToken();
        if (token) {
            authView.classList.add("hidden");
            appView.classList.remove("hidden");
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                userEmailSpan.textContent = payload.sub;
                fetchGroups();
            } catch (e) {
                localStorage.removeItem("access_token");
                updateUI();
            }
        } else {
            authView.classList.remove("hidden");
            appView.classList.add("hidden");
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
            groupsListDiv.innerHTML = ""; // Clear existing list
            
            if (groups.length === 0) {
                groupsListDiv.innerHTML = "<div class='card' style='text-align:center;'><p>You haven't created any groups yet. Create one above to get started!</p></div>";
            } else {
                groups.forEach(group => {
                    const groupEl = document.createElement("div");
                    groupEl.className = "group-item";
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

    // --- Event Listeners for Auth and Tabs ---
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(tab.dataset.tab).classList.add("active");
        });
    });
    
    const handleAuthFormSubmit = async (url, formData, successMessage, formToReset) => {
        showLoader();
        try {
            const response = await fetch(url, { method: "POST", body: formData });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "An error occurred.");
            
            showToast(successMessage, "success");
            if (formToReset) formToReset.reset();
            return data;
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            hideLoader();
        }
    };

    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('username', document.getElementById('register-email').value);
        formData.append('password', document.getElementById('register-password').value);
        await handleAuthFormSubmit("/register", formData, "Registration successful! Please log in.", registerForm);
    });

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('username', document.getElementById('login-email').value);
        formData.append('password', document.getElementById('login-password').value);
        
        const data = await handleAuthFormSubmit("/token", formData, "Login successful!", loginForm);
        if (data && data.access_token) {
            localStorage.setItem("access_token", data.access_token);
            updateUI();
        }
    });

    logoutButton.addEventListener("click", () => {
        localStorage.removeItem("access_token");
        showToast("Logged out successfully.", "success");
        updateUI();
    });

    // --- New Logic for Interactive Group Creation ---
    
    const createGroupForm = document.getElementById("create-group-form");
    const memberNameInput = document.getElementById("member-name-input");
    const addMemberButton = document.getElementById("add-member-button");
    const membersListContainer = document.getElementById("members-list-container");
    const createGroupButton = document.getElementById("create-group-button");
    
    // State to hold members for the new group form
    let currentMembers = []; 
    
    const renderMembersList = () => {
        membersListContainer.innerHTML = ""; // Clear current list
        currentMembers.forEach(member => {
            const pill = document.createElement("div");
            pill.className = "member-pill";
            // Sanitize member name to prevent HTML injection before setting innerHTML
            const safeMemberName = member.replace(/</g, "<").replace(/>/g, ">");
            pill.innerHTML = `
                <span>${safeMemberName}</span>
                <button type="button" class="remove-member-btn" data-member="${safeMemberName}">×</button>
            `;
            membersListContainer.appendChild(pill);
        });
        validateCreateGroupButton();
    };

    const validateCreateGroupButton = () => {
        createGroupButton.disabled = currentMembers.length < 2;
    };

    const addMember = () => {
        const newMemberName = memberNameInput.value.trim();
        
        if (!newMemberName) {
            showToast("Member name cannot be empty.", "error");
            return;
        }
        if (currentMembers.map(m => m.toLowerCase()).includes(newMemberName.toLowerCase())) {
            showToast("This member has already been added.", "error");
            return;
        }
        
        currentMembers.push(newMemberName);
        renderMembersList();
        memberNameInput.value = ""; // Clear the input field
        memberNameInput.focus();
    };
    
    addMemberButton.addEventListener("click", addMember);
    
    memberNameInput.addEventListener("keydown", (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent form submission
            addMember();
        }
    });

    membersListContainer.addEventListener("click", (e) => {
        if (e.target && e.target.classList.contains("remove-member-btn")) {
            const memberToRemove = e.target.dataset.member;
            currentMembers = currentMembers.filter(m => m !== memberToRemove);
            renderMembersList();
        }
    });

    createGroupForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        if (currentMembers.length < 2) {
            showToast("You must add at least two members to the group.", "error");
            return;
        }
        
        showLoader();
        try {
            const token = getToken();
            const groupName = document.getElementById("group-name").value;
            const members = currentMembers;

            const response = await fetch("/groups", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ name: groupName, members: members })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || "Failed to create group.");
            
            showToast("Group created successfully!", "success");
            // Reset the form and the state
            document.getElementById("group-name").value = "";
            currentMembers = [];
            renderMembersList();
            
            fetchGroups(); // Refresh the main groups list
        } catch (error) {
            showToast(error.message, "error");
        } finally {
            hideLoader();
        }
    });

    // --- Initial Load ---
    updateUI();
});