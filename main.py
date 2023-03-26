from math import floor
from random import randint, seed

from perlin_noise import PerlinNoise
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

# Chunk constants.
CHUNK_SIZE = 16  # Default: 16.
# Limits the height of each hill.
HEIGHT_LIMIT = 256  # Default: 256.
HILL_FREQ = 1 / 56  # Default: 1 / 56.
# Used for how many chunks will be in front of you.
RENDER_DISTANCE = 1  # Default: 1.
# Number of chunks to generate.
CHUNKS_TO_GENERATE = floor(((RENDER_DISTANCE*2 + 1)**2 - 1) / 2)

app = Ursina(
    show_ursina_splash=False,
    title="Walking Sim",
    forced_aspect_ratio=False,
    vsync=True
)

# Used to seed a Perlin noise generator,
# so that the same seed can take you back to the same world.
seed(randint(1, 2**64 - 1))

# Used to shape the terrain.
terrain_noise = PerlinNoise(1, seed=randint(1, 2**64 - 1))

def generate_chunk(chunk_x: float, chunk_z: float) -> Entity:
    """Generate a chunk in the world."""

    # These variables are used to place chunks in the world.
    # Also, they're used to represent the bottom left corner of the chunk.
    chunk_x = int(chunk_x * (CHUNK_SIZE - 1))
    chunk_z = int(chunk_z * (CHUNK_SIZE - 1))
    
    # Used to store height values.
    hv = []

    for block_x in range(chunk_x, chunk_x + CHUNK_SIZE):
        chunk_slice = []

        for block_z in range(chunk_z, chunk_z + CHUNK_SIZE):
            # Determines the height of a part of the chunk.
            height = terrain_noise([block_x * HILL_FREQ, block_z * HILL_FREQ]) * HEIGHT_LIMIT

            chunk_slice.append(height)
        
        hv.append(chunk_slice)
    
    # Make the chunk and return it.
    return Entity(
        model=Terrain(height_values=hv),
        position=(chunk_x + CHUNK_SIZE/2, 0, chunk_z + CHUNK_SIZE/2),
        scale=(CHUNK_SIZE, CHUNK_SIZE, CHUNK_SIZE),
        texture="grass top chunk.png",
        collider="mesh"
    )

def generate_chunks_around_player(player_chunk_coords_now: list) -> int:
    """Generates chunks around the player's current position in a square spiral.
    Returns how many chunks were generated.
    """

    chunk_amount = 0

    # Inital chunk will be at player.
    chunk_coords = player_chunk_coords_now

    # Generate initial chunk if it doesn't exist.
    if chunk_coords not in chunk_coords_array:
        chunk_coords_array.append(chunk_coords[:])
        
        chunks.append(generate_chunk(*chunk_coords))
        chunk_amount += 1

    # Generates chunks around the player.
    for change_amount in range(1, CHUNKS_TO_GENERATE):
        if change_amount % 2 == 0:
            change_amount = -change_amount
        
        if change_amount < 0:
            for i in range(abs(change_amount)):
                # Change x coord.
                chunk_coords[0] -= 1
                
                # If chunk_coords isn't in chunk_coords_array,
                # then there isn't a chunk at that location.
                # So one will be made there.
                if chunk_coords not in chunk_coords_array:
                    chunk_coords_array.append(chunk_coords[:])
                    
                    chunks.append(generate_chunk(*chunk_coords))
                    chunk_amount += 1
        else:
            for i in range(abs(change_amount)):
                chunk_coords[0] += 1
                
                if chunk_coords not in chunk_coords_array:
                    chunk_coords_array.append(chunk_coords[:])
                    
                    chunks.append(generate_chunk(*chunk_coords))
                    chunk_amount += 1
            
        change_amount = -change_amount
        
        if change_amount < 0:
            for i in range(abs(change_amount)):
                # Change y coord.
                chunk_coords[1] -= 1
                
                if chunk_coords not in chunk_coords_array:
                    chunk_coords_array.append(chunk_coords[:])
                    
                    chunks.append(generate_chunk(*chunk_coords))
                    chunk_amount += 1
        else:
            for i in range(abs(change_amount)):
                chunk_coords[1] += 1
                
                if chunk_coords not in chunk_coords_array:
                    chunk_coords_array.append(chunk_coords[:])
                    
                    chunks.append(generate_chunk(*chunk_coords))
                    chunk_amount += 1
    
    return chunk_amount

player = FirstPersonController(y=100)

# Used to hold every currently loaded chunk.
chunks = []

# Holds coords of every currently loaded chunk.
# Also used to determine whether a chunk should be generated or not.
chunk_coords_array = []

Sky()

def update(chunk_amount_prev=generate_chunks_around_player([0, 0]), player_chunk_coords_prev=None):
    # See if the player has entered a new chunk.
    player_chunk_coords_now = [player.x // CHUNK_SIZE, player.z // CHUNK_SIZE]

    # If the player has entered a new chunk, then we need to create more chunks for them.
    if player_chunk_coords_now != player_chunk_coords_prev:
        chunk_amount_now = generate_chunks_around_player(player_chunk_coords_now)

        indexes_to_remove = []
        
        # After new chunks are created, there's a chance that some older chunks are
        # now out of the player's render distance.
        for index, chunk in enumerate(chunks[:chunk_amount_now - chunk_amount_prev]):
            # If a chunk is out of the player's render distance,
            if distance_2d(player, chunk) > RENDER_DISTANCE*16:
                # then it will be removed later.
                indexes_to_remove.append(index)
        
        # Also remove chunk remove the chunks list and
        # remove its coords from chunk_coords_array.
        for index in indexes_to_remove:
            destroy(chunks[index])
            del chunks[index], chunk_coords_array[index]

        chunk_amount_prev = chunk_amount_now
        player_chunk_coords_prev = player_chunk_coords_now

app.run()