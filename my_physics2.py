import math
import random
import pygame


# Define global constants.
NUM_PARTICLES = 6
SPEED_COEFFICIENT = 0.1
DRAG_COEFFICIENT = 0.9999
ELASTICITY_COEFFICIENT = 0.999
GRAVITY = 0.000002


class Particle:
    """The element in the physics simulation that interacts with other instances.

    Each particle has pixel coordinates (x, y), and a vector that consists of
    an angle (in radians) and speed that determine the direction and velocity
    of the particle's movement.
    """

    def __init__(self, position: (int, int), radius, angle, speed):
        self.x, self.y = position
        self.radius = radius
        self.angle = angle
        self.speed = speed
    
    def move(self) -> None:
        """Move the particle using angle and speed."""
        self._apply_drag()
        self._apply_gravity()

        # Find dx and dy.
        dx = math.cos(self.angle)
        dy = -math.sin(self.angle) # - sign because y axis is flipped.
        # Move the particle.
        self.x += dx * self.speed
        self.y += dy * self.speed
    
    def bounce(self, window_dimensions: (int, int)) -> None:
        """Bounce the particle off the edge of the window."""
        width, height = window_dimensions
        # Left side.
        if self.x <= self.radius:
            # Update angle.
            self.angle = math.pi - self.angle
            # Update position to prevent particle being out of bounds.
            self.x += 2 * (self.radius - self.x)
            self.apply_elasticity()
        # Right side.
        elif self.x >= width - self.radius:
            # Update angle.
            self.angle = math.pi - self.angle
            # Update position to prevent particle being out of bounds.
            self.x -= 2 * (self.x + self.radius - width)
            self.apply_elasticity()
        # Top.
        if self.y <= self.radius:
            # Update angle.
            self.angle = -self.angle
            # Update position to prevent particle being out of bounds.
            self.y += 2 * (self.radius - self.y)
            self.apply_elasticity()
        # Bottom
        elif self.y >= height - self.radius:
            # Update angle.
            self.angle = -self.angle
            # Update position to prevent particle being out of bounds.
            self.y -= 2 * (self.y + self.radius - height)
            self.apply_elasticity()

    def display(self, surface) -> None:
        """Draw the particle on the provided surface as a pygame circle.
        
        The pygame draw.circle function takes surface, color, center, radius,
        and width (of the line) as arguments.

        pygame.draw.circle(surface, color:tuple, center:tuple, radius:int, width:int)
        """
        pygame.draw.circle(
            surface,
            (0, 0, 255),
            # Math.floor ensures integer arguments are given.
            (math.floor(self.x), math.floor(self.y)),
            self.radius,
            1
        )

    def collide(self, p2) -> None:
        """Handle collision physics with another particle."""
        # First, check for distance between the particles.
        dx = self.x - p2.x
        dy = -(self.y - p2.y) # Flipped y-axis
        dist = math.hypot(dx, dy)

        # Case where they just collided.
        if dist <= self.radius + p2.radius:
            angle_collision = math.atan2(dy, dx)
            tangent_angle = angle_collision + (math.pi / 2)

            # Reflect the particles off of each other.
            self.angle = -self.angle + 2 * tangent_angle
            p2.angle = -p2.angle + 2 * tangent_angle

            # Exchange their speeds.
            self.speed, p2.speed = p2.speed, self.speed

            # Fix any overlapping between the particles.
            overlap_amnt = self.radius + p2.radius - dist
            self.x += math.cos(angle_collision) * overlap_amnt / 2
            self.y -= math.sin(angle_collision) * overlap_amnt / 2
            p2.x -= math.cos(angle_collision) * overlap_amnt / 2
            p2.y += math.sin(angle_collision) * overlap_amnt / 2

            # Apply elasticity to the collision.
            self.apply_elasticity()
            p2.apply_elasticity()


    def follow(self, mouse_coords: (int, int)) -> None:
        """Make the particle follow the mouse cursor."""
        mouseX, mouseY = mouse_coords
        dx = mouseX - self.x
        dy = -(mouseY - self.y) # Negative because y axis is flipped.
        # Multiplying by SPEED_COEFFICIENT slows the particle down long enough
        # for the mouse to get a sufficient lead and drag/fling the particle
        # in a realistic manner.
        self.speed = math.hypot(dx, dy) * SPEED_COEFFICIENT
        self.angle = math.atan2(dy, dx)

    def apply_elasticity(self) -> None:
        """Multiply speed by ELASTICITY_COEFFICIENT."""
        self.speed *= ELASTICITY_COEFFICIENT

    def _apply_drag(self) -> None:
        """Multiply speed by DRAG_COEFFICIENT to simulate air resistance."""
        self.speed *= DRAG_COEFFICIENT

    def _apply_gravity(self) -> None:
        """Add the gravity vector to the particle vector."""
        # Calculate x and y components of each vector.
        particle_x_component = math.cos(self.angle) * self.speed
        particle_y_component = math.sin(self.angle) * self.speed
        grav_x_component = math.cos(-math.pi/2) * GRAVITY
        grav_y_component = math.sin(-math.pi/2) * GRAVITY
        # Add them together to get the new vector components.
        new_x_comp = particle_x_component + grav_x_component
        new_y_comp = particle_y_component + grav_y_component
        # Define new vector.
        self.angle = math.atan2(new_y_comp, new_x_comp)
        self.speed = math.hypot(new_x_comp, new_y_comp)
        

class Simulation:
    def __init__(self):
        # Define intial values.
        self._particles = []
        self._width, self._height = (800, 800)
        self._create_particles(NUM_PARTICLES) # Uses width and height.
        self._selected_particle = None
        # Initialize pygame.
        pygame.init()
        # self._clock = pygame.time.Clock()
        self._surface = pygame.display.set_mode((self._width, self._height))
        pygame.display.set_caption('Particle Simulation')
        self._surface.fill((255, 255, 255)) # White background.

    def run(self) -> None:
        """Run the simulation."""
        self._running = True

        while self._running:
            # self._clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self._select_particle(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self._selected_particle = None # Deslect (drop) particle.
            
            self._handle_events()
            self._redraw_frame()
            
        pygame.quit()

    def _handle_events(self) -> None:
        """Handle all the non-visual aspects of the simulation."""
        if self._selected_particle: 
            # The selected particle gets special treatment to move it around.
            self._selected_particle.follow(pygame.mouse.get_pos())
        for index, particle in enumerate(self._particles):
            particle.move()
            particle.bounce((self._width, self._height))
            for other_particle in self._particles[index + 1:]:
                particle.collide(other_particle)
    
    def _redraw_frame(self) -> None:
        """Draw the background, particles, and then flip the display."""
        self._surface.fill((255, 255, 255))
        for particle in self._particles:
            particle.display(self._surface)
        pygame.display.flip()

    def _select_particle(self, mouse_coodinates: (int, int)) -> None:
        """Select a particle that the mouse clicks on."""
        mouseX, mouseY = mouse_coodinates
        for particle in self._particles:
            dx = mouseX - particle.x
            dy = mouseY - particle.y
            dist = math.hypot(dx, dy)
            # If the mouse clicked within the particle, select the particle.
            if dist <= particle.radius:
                self._selected_particle = particle
    
    def _create_particles(self, n) -> None:
        """Modify the _particles list to include n random particles."""
        for _ in range(n):
            # Randomly choose the radius, angle, and speed.
            angle = random.uniform(0, math.pi * 2)
            speed = random.random()
            radius = random.randint(10, 20)
            density = random.randint(1, 20)
            # Choose a random position within the bounds of the window.
            x = random.randint(radius, self._width - radius)
            y = random.randint(radius, self._height - radius)
            # Create and append a particle to the list of particles.
            self._particles.append(Particle((x, y), radius, angle, speed))


if __name__ == '__main__':
    Simulation().run()